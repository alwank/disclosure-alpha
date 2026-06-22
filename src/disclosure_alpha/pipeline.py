"""In-memory deterministic pipeline: HTML → sections → metrics → scores."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from disclosure_alpha.confidence import ConfidenceInput, compute_confidence_detailed, compute_overall_confidence
from disclosure_alpha.deterministic_scoring import (
    DeterministicAggregationResult,
    aggregate_deterministic_matrix,
    aggregate_deterministic_matrix_v2,
)
from disclosure_alpha.diff_engine import compute_section_diff
from disclosure_alpha.section_extractor import (
    ExtractedSection,
    FilingDocument,
    extract_sections,
)
from disclosure_alpha.text_metrics import (
    SectionTextInput,
    compute_density_metrics,
    compute_text_metrics,
    detect_section_flags,
)
from disclosure_alpha.edgar.types import EdgarError
from disclosure_alpha.version import (
    METRICS_ENGINE_VERSION,
    PARSER_VERSION,
    SCORING_MODEL_VERSION,
    SCORING_MODEL_VERSION_V2,
)

_VERSIONS = {
    "parser_version": PARSER_VERSION,
    "metrics_engine_version": METRICS_ENGINE_VERSION,
    "scoring_model_version": SCORING_MODEL_VERSION,
}


@dataclass
class FilingBundle:
    ref: Any  # FilingRef — lazy import to avoid circular deps
    html: str
    prior_html: str | None
    prior_accession: str | None


@dataclass
class FilingSectionsResult:
    sections: list[ExtractedSection]
    filing: dict[str, Any] = field(default_factory=dict)
    versions: dict[str, str] = field(default_factory=dict)


@dataclass
class FilingMetricsResult:
    metrics: MetricsResult
    filing: dict[str, Any] = field(default_factory=dict)
    versions: dict[str, str] = field(default_factory=dict)


@dataclass
class MetricsResult:
    section_metrics: dict[str, dict[str, float]]
    section_diffs: dict[str, float | None]
    section_flags: dict[str, dict[str, bool]]
    section_densities: dict[str, dict[str, float]]
    language_deltas: dict[str, dict[str, float]]
    section_diffs_v2: dict[str, float | None] = field(default_factory=dict)
    extraction_confs: list[float] = field(default_factory=list)
    diff_confs: list[float] = field(default_factory=list)
    extraction_warnings: list[str] = field(default_factory=list)
    required_sections_present: bool = True
    has_prior: bool = True


@dataclass
class FilingScoreResult:
    sections: list[ExtractedSection]
    metrics: MetricsResult
    scores: DeterministicAggregationResult
    versions: dict[str, str] = field(default_factory=dict)
    filing: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        out = {
            "sections": [asdict(s) for s in self.sections],
            "metrics": asdict(self.metrics),
            "scores": {
                "overall_disclosure_risk_score": self.scores.overall_disclosure_risk_score,
                "score_coverage_ratio": self.scores.score_coverage_ratio,
                "confidence_score": self.scores.confidence_score,
                "missing_components": self.scores.missing_components,
                "components": asdict(self.scores.components),
                "aggregates": asdict(self.scores.aggregates),
                "provenance": [p.to_dict() for p in self.scores.provenance],
            },
            "versions": self.versions,
        }
        if self.filing:
            out["filing"] = self.filing
        return out


def _metrics_dict(metrics) -> dict[str, float]:
    return {
        "negative_word_ratio": float(metrics.negative_word_ratio or 0),
        "uncertainty_word_ratio": float(metrics.uncertainty_word_ratio or 0),
        "litigious_word_ratio": float(metrics.litigious_word_ratio or 0),
        "modal_word_ratio": float(metrics.modal_word_ratio or 0),
        "constraining_word_ratio": float(metrics.constraining_word_ratio or 0),
        "boilerplate_phrase_ratio": float(metrics.boilerplate_phrase_ratio or 0),
        "numeric_specificity_score": float(metrics.numeric_specificity_score or 0),
        "company_specificity_score": float(metrics.company_specificity_score or 0),
        "readability_score": float(metrics.readability_score or 0),
    }


def _prior_by_name(
    prior_sections: list[ExtractedSection] | None, section_name: str
) -> ExtractedSection | None:
    if not prior_sections:
        return None
    for section in prior_sections:
        if section.section_name == section_name:
            return section
    return None


def extract_sections_from_html(
    html: str,
    form_type: str,
    *,
    cik: str = "",
    accession_number: str = "",
) -> list[ExtractedSection]:
    return extract_sections(
        FilingDocument(
            cik=cik,
            accession_number=accession_number,
            form_type=form_type,
            html=html,
        )
    )


def compute_section_metrics(
    sections: list[ExtractedSection],
    prior_sections: list[ExtractedSection] | None = None,
) -> MetricsResult:
    section_metrics: dict[str, dict[str, float]] = {}
    section_diffs: dict[str, float | None] = {}
    section_flags: dict[str, dict[str, bool]] = {}
    section_densities: dict[str, dict[str, float]] = {}
    language_deltas: dict[str, dict[str, float]] = {}
    section_diffs_v2: dict[str, float | None] = {}
    extraction_confs: list[float] = []
    diff_confs: list[float] = []

    for section in sections:
        extraction_confs.append(float(section.extraction_confidence or 0.5))
        text = section.cleaned_text or ""
        metrics = compute_text_metrics(SectionTextInput(section.section_name, text))
        section_metrics[section.section_name] = _metrics_dict(metrics)
        section_flags[section.section_name] = detect_section_flags(text, section.section_name)
        section_densities[section.section_name] = compute_density_metrics(text, section.section_name)

        prior = _prior_by_name(prior_sections, section.section_name)
        diff = compute_section_diff(
            current_text=text,
            prior_text=prior.cleaned_text if prior else None,
            current_section_id=section.section_name,
            prior_section_id=prior.section_name if prior else None,
        )
        if diff.disclosure_change_score is not None:
            section_diffs[section.section_name] = float(diff.disclosure_change_score)
        if diff.disclosure_change_score_v2 is not None:
            section_diffs_v2[section.section_name] = float(diff.disclosure_change_score_v2)
        if diff.language_deltas:
            language_deltas[section.section_name] = dict(diff.language_deltas)
        if diff.confidence_score is not None:
            diff_confs.append(float(diff.confidence_score))

    return MetricsResult(
        section_metrics=section_metrics,
        section_diffs=section_diffs,
        section_flags=section_flags,
        section_densities=section_densities,
        language_deltas=language_deltas,
        section_diffs_v2=section_diffs_v2,
        extraction_confs=extraction_confs,
        diff_confs=diff_confs,
        has_prior=prior_sections is not None and len(prior_sections) > 0,
    )


def score_deterministic(metrics: MetricsResult) -> DeterministicAggregationResult:
    result = aggregate_deterministic_matrix(
        section_metrics=metrics.section_metrics,
        section_diffs=metrics.section_diffs,
        section_flags=metrics.section_flags,
        language_deltas=metrics.language_deltas,
        section_densities=metrics.section_densities,
    )
    avg_diff_conf = (
        sum(metrics.diff_confs) / len(metrics.diff_confs) if metrics.diff_confs else None
    )
    result.confidence_score = compute_overall_confidence(
        extraction_confidences=metrics.extraction_confs,
        coverage_ratio=result.score_coverage_ratio,
        diff_confidence=avg_diff_conf,
        extraction_warnings=metrics.extraction_warnings,
        required_sections_present=metrics.required_sections_present,
        has_prior=metrics.has_prior,
    )
    return result


def score_deterministic_v2(metrics: MetricsResult) -> DeterministicAggregationResult:
    """Versioned scoring entry point with evidence model and calibration."""
    result = aggregate_deterministic_matrix_v2(
        section_metrics=metrics.section_metrics,
        section_diffs=metrics.section_diffs,
        section_flags=metrics.section_flags,
        language_deltas=metrics.language_deltas,
        section_densities=metrics.section_densities,
        section_diffs_v2=metrics.section_diffs_v2,
    )
    avg_diff_conf = (
        sum(metrics.diff_confs) / len(metrics.diff_confs) if metrics.diff_confs else None
    )
    result.confidence_score, _ = compute_confidence_detailed(
        ConfidenceInput(
            extraction_confidences=metrics.extraction_confs,
            extraction_warnings=metrics.extraction_warnings,
            coverage_ratio=result.score_coverage_ratio,
            required_sections_present=metrics.required_sections_present,
            diff_confidence=avg_diff_conf,
            has_prior=metrics.has_prior,
        )
    )
    return result


def score_filing_html(
    html: str,
    form_type: str,
    *,
    prior_html: str | None = None,
    prior_form_type: str | None = None,
    cik: str = "",
    accession_number: str = "",
) -> FilingScoreResult:
    sections = extract_sections_from_html(
        html, form_type, cik=cik, accession_number=accession_number
    )
    prior_sections = None
    if prior_html:
        prior_sections = extract_sections_from_html(
            prior_html,
            prior_form_type or form_type,
            cik=cik,
            accession_number="prior",
        )
    metrics = compute_section_metrics(sections, prior_sections)
    scores = score_deterministic(metrics)
    return FilingScoreResult(
        sections=sections,
        metrics=metrics,
        scores=scores,
        versions=dict(_VERSIONS),
    )


def _filing_meta(ref, *, prior_accession: str | None = None) -> dict[str, Any]:
    return {
        "ticker": ref.ticker,
        "cik": ref.cik,
        "accession_number": ref.accession_number,
        "form_type": ref.form_type,
        "fiscal_year": ref.fiscal_year,
        "quarter": ref.quarter,
        "filing_date": ref.filing_date,
        "report_date": ref.report_date,
        "prior_accession_number": prior_accession,
    }


def _filter_section_dict(d: dict[str, Any], section_names: set[str]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if k in section_names}


def filter_metrics_result(metrics: MetricsResult, section_names: set[str]) -> MetricsResult:
    return MetricsResult(
        section_metrics=_filter_section_dict(metrics.section_metrics, section_names),
        section_diffs=_filter_section_dict(metrics.section_diffs, section_names),
        section_flags=_filter_section_dict(metrics.section_flags, section_names),
        section_densities=_filter_section_dict(metrics.section_densities, section_names),
        language_deltas=_filter_section_dict(metrics.language_deltas, section_names),
        section_diffs_v2=_filter_section_dict(metrics.section_diffs_v2, section_names),
        extraction_confs=metrics.extraction_confs,
        diff_confs=metrics.diff_confs,
        extraction_warnings=metrics.extraction_warnings,
        required_sections_present=metrics.required_sections_present,
        has_prior=metrics.has_prior,
    )


def filter_sections(
    sections: list[ExtractedSection], section_names: set[str]
) -> list[ExtractedSection]:
    return [s for s in sections if s.section_name in section_names]


def load_filing_bundle(
    ticker: str,
    fiscal_year: int,
    *,
    form_type: str = "10-K",
    quarter: str | None = None,
    use_cache: bool = True,
    compare_prior: bool = True,
) -> FilingBundle:
    from disclosure_alpha.edgar.resolver import (
        load_filing_html,
        resolve_filing,
        resolve_prior_filing,
    )
    from disclosure_alpha.edgar.types import FilingNotFoundError

    ref = resolve_filing(ticker, fiscal_year, form_type, quarter, use_cache=use_cache)
    html = load_filing_html(ref, use_cache=use_cache)

    prior_html = None
    prior_accession = None
    if compare_prior:
        try:
            prior_ref = resolve_prior_filing(ref, use_cache=use_cache)
            if prior_ref:
                prior_html = load_filing_html(prior_ref, use_cache=use_cache)
                prior_accession = prior_ref.accession_number
        except FilingNotFoundError:
            pass

    return FilingBundle(
        ref=ref,
        html=html,
        prior_html=prior_html,
        prior_accession=prior_accession,
    )


def sections_filing_ticker(
    ticker: str,
    fiscal_year: int,
    *,
    form_type: str = "10-K",
    quarter: str | None = None,
    use_cache: bool = True,
    compare_prior: bool = True,
) -> FilingSectionsResult:
    bundle = load_filing_bundle(
        ticker,
        fiscal_year,
        form_type=form_type,
        quarter=quarter,
        use_cache=use_cache,
        compare_prior=compare_prior,
    )
    sections = extract_sections_from_html(
        bundle.html,
        bundle.ref.form_type,
        cik=bundle.ref.cik,
        accession_number=bundle.ref.accession_number,
    )
    return FilingSectionsResult(
        sections=sections,
        filing=_filing_meta(bundle.ref, prior_accession=bundle.prior_accession),
        versions=dict(_VERSIONS),
    )


def metrics_filing_ticker(
    ticker: str,
    fiscal_year: int,
    *,
    form_type: str = "10-K",
    quarter: str | None = None,
    use_cache: bool = True,
    compare_prior: bool = True,
) -> FilingMetricsResult:
    bundle = load_filing_bundle(
        ticker,
        fiscal_year,
        form_type=form_type,
        quarter=quarter,
        use_cache=use_cache,
        compare_prior=compare_prior,
    )
    sections = extract_sections_from_html(
        bundle.html,
        bundle.ref.form_type,
        cik=bundle.ref.cik,
        accession_number=bundle.ref.accession_number,
    )
    prior_sections = None
    if bundle.prior_html:
        prior_sections = extract_sections_from_html(
            bundle.prior_html,
            bundle.ref.form_type,
            cik=bundle.ref.cik,
            accession_number="prior",
        )
    metrics = compute_section_metrics(sections, prior_sections)
    return FilingMetricsResult(
        metrics=metrics,
        filing=_filing_meta(bundle.ref, prior_accession=bundle.prior_accession),
        versions=dict(_VERSIONS),
    )


def score_filing_ticker(
    ticker: str,
    fiscal_year: int,
    *,
    form_type: str = "10-K",
    quarter: str | None = None,
    use_cache: bool = True,
    compare_prior: bool = True,
) -> FilingScoreResult:
    bundle = load_filing_bundle(
        ticker,
        fiscal_year,
        form_type=form_type,
        quarter=quarter,
        use_cache=use_cache,
        compare_prior=compare_prior,
    )
    result = score_filing_html(
        bundle.html,
        bundle.ref.form_type,
        prior_html=bundle.prior_html,
        cik=bundle.ref.cik,
        accession_number=bundle.ref.accession_number,
    )
    result.filing = _filing_meta(bundle.ref, prior_accession=bundle.prior_accession)
    return result


@dataclass
class PanelTickerResult:
    ticker: str
    status: str
    filing: dict[str, Any] | None = None
    scores: DeterministicAggregationResult | None = None
    error: str | None = None


@dataclass
class PanelBatchResult:
    results: list[PanelTickerResult]
    summary: dict[str, int]
    versions: dict[str, str]


def score_panel_tickers(
    tickers: list[str],
    fiscal_year: int,
    *,
    form_type: str = "10-K",
    quarter: str | None = None,
    use_cache: bool = True,
    compare_prior: bool = True,
) -> PanelBatchResult:
    """Score many tickers sequentially; per-ticker errors do not fail the batch."""
    results: list[PanelTickerResult] = []
    ok = 0
    failed = 0
    for raw in tickers:
        ticker = raw.strip().upper()
        try:
            scored = score_filing_ticker(
                ticker,
                fiscal_year,
                form_type=form_type,
                quarter=quarter,
                use_cache=use_cache,
                compare_prior=compare_prior,
            )
            results.append(
                PanelTickerResult(
                    ticker=ticker,
                    status="ok",
                    filing=scored.filing,
                    scores=scored.scores,
                )
            )
            ok += 1
        except (EdgarError, ValueError, FileNotFoundError) as exc:
            results.append(
                PanelTickerResult(
                    ticker=ticker,
                    status="error",
                    error=str(exc),
                )
            )
            failed += 1
    return PanelBatchResult(
        results=results,
        summary={"ok": ok, "failed": failed},
        versions=dict(_VERSIONS),
    )
