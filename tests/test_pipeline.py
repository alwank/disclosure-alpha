import json

import pytest

from disclosure_alpha.pipeline import score_filing_html
from disclosure_alpha.version import PARSER_VERSION


def test_score_filing_html_minimal():
    html = """
    <html><body>
    <p>Item 1A. Risk Factors</p>
    <p>We may face litigation and regulatory investigation. Results could be uncertain.</p>
    <p>Item 7. Management's Discussion and Analysis</p>
    <p>Revenue may decline amid margin pressure and liquidity constraints.</p>
    </body></html>
    """
    result = score_filing_html(html, "10-K")
    assert result.scores.overall_disclosure_risk_score is not None
    assert result.versions["parser_version"] == PARSER_VERSION
    payload = result.to_dict()
    assert "scores" in payload
    assert json.dumps(payload)


def test_score_filing_with_prior():
    prior = "<html><body><p>Item 1A. Risk Factors</p><p>Stable operations.</p></body></html>"
    current = "<html><body><p>Item 1A. Risk Factors</p><p>We may face litigation and investigation.</p></body></html>"
    result = score_filing_html(current, "10-K", prior_html=prior)
    assert result.metrics.section_diffs.get("item_1a_risk_factors") is not None


def test_score_filing_ticker_mocked(monkeypatch):
    from pathlib import Path

    from disclosure_alpha.edgar.types import FilingRef
    from disclosure_alpha.pipeline import score_filing_ticker

    html_path = (
        Path(__file__).resolve().parents[1]
        / "tests/fixtures/filings/aapl_2025_10k.html"
    )
    html = html_path.read_text(encoding="utf-8", errors="replace")
    ref = FilingRef(
        cik="0000320193",
        ticker="AAPL",
        accession_number="0000320193-25-000079",
        form_type="10-K",
        fiscal_year=2025,
        quarter=None,
        filing_date="2025-10-31",
        report_date="2025-09-27",
        primary_document="aapl.htm",
    )

    monkeypatch.setattr(
        "disclosure_alpha.pipeline.load_filing_bundle",
        lambda *a, **k: __import__(
            "disclosure_alpha.pipeline", fromlist=["FilingBundle"]
        ).FilingBundle(
            ref=ref,
            html=html,
            prior_html=None,
            prior_accession=None,
        ),
    )

    result = score_filing_ticker("AAPL", 2025)
    assert result.filing["ticker"] == "AAPL"
    assert result.scores.overall_disclosure_risk_score is not None


def test_load_filing_bundle_compare_prior(monkeypatch):
    from disclosure_alpha.edgar.types import FilingRef
    from disclosure_alpha.pipeline import FilingBundle, load_filing_bundle

    ref = FilingRef(
        cik="0000320193",
        ticker="AAPL",
        accession_number="0000320193-25-000079",
        form_type="10-K",
        fiscal_year=2025,
        quarter=None,
        filing_date="2025-10-31",
        report_date="2025-09-27",
        primary_document="aapl.htm",
    )
    prior_calls: list[str] = []

    monkeypatch.setattr(
        "disclosure_alpha.edgar.resolver.resolve_filing",
        lambda *a, **k: ref,
    )
    monkeypatch.setattr(
        "disclosure_alpha.edgar.resolver.load_filing_html",
        lambda r, **k: "<html></html>",
    )

    def _prior(*a, **k):
        prior_calls.append("called")
        return ref

    monkeypatch.setattr(
        "disclosure_alpha.edgar.resolver.resolve_prior_filing",
        _prior,
    )

    bundle = load_filing_bundle("AAPL", 2025, compare_prior=True)
    assert bundle.prior_html is not None
    assert prior_calls

    prior_calls.clear()
    bundle = load_filing_bundle("AAPL", 2025, compare_prior=False)
    assert bundle.prior_html is None
    assert not prior_calls


def test_metrics_filing_ticker_mocked(monkeypatch):
    from disclosure_alpha.edgar.types import FilingRef
    from disclosure_alpha.pipeline import FilingBundle, metrics_filing_ticker

    html = """
    <html><body>
    <p>Item 1A. Risk Factors</p>
    <p>We may face litigation and regulatory investigation.</p>
    <p>Item 7. Management's Discussion and Analysis</p>
    <p>Revenue may decline amid margin pressure.</p>
    </body></html>
    """
    ref = FilingRef(
        cik="0000320193",
        ticker="AAPL",
        accession_number="0000320193-25-000079",
        form_type="10-K",
        fiscal_year=2025,
        quarter=None,
        filing_date="2025-10-31",
        report_date="2025-09-27",
        primary_document="aapl.htm",
    )
    monkeypatch.setattr(
        "disclosure_alpha.pipeline.load_filing_bundle",
        lambda *a, **k: FilingBundle(
            ref=ref, html=html, prior_html=None, prior_accession=None
        ),
    )
    result = metrics_filing_ticker("AAPL", 2025)
    assert result.filing["ticker"] == "AAPL"
    assert result.metrics.section_metrics
    assert result.sections


def test_sections_filing_ticker_mocked(monkeypatch):
    from disclosure_alpha.edgar.types import FilingRef
    from disclosure_alpha.pipeline import FilingBundle, sections_filing_ticker

    html = """
    <html><body>
    <p>Item 1A. Risk Factors</p>
    <p>We may face litigation.</p>
    </body></html>
    """
    ref = FilingRef(
        cik="0000320193",
        ticker="AAPL",
        accession_number="0000320193-25-000079",
        form_type="10-K",
        fiscal_year=2025,
        quarter=None,
        filing_date="2025-10-31",
        report_date="2025-09-27",
        primary_document="aapl.htm",
    )
    monkeypatch.setattr(
        "disclosure_alpha.pipeline.load_filing_bundle",
        lambda *a, **k: FilingBundle(
            ref=ref, html=html, prior_html=None, prior_accession=None
        ),
    )
    result = sections_filing_ticker("AAPL", 2025)
    assert result.filing["ticker"] == "AAPL"
    assert any(s.section_name == "item_1a_risk_factors" for s in result.sections)


def test_filter_metrics_result():
    from disclosure_alpha.pipeline import MetricsResult, filter_metrics_result

    metrics = MetricsResult(
        section_metrics={
            "item_1a_risk_factors": {"negative_word_ratio": 0.1},
            "item_7_mdna": {"negative_word_ratio": 0.2},
        },
        section_diffs={"item_1a_risk_factors": 50.0},
        section_flags={"item_1a_risk_factors": {"investigation_flag": True}},
        section_densities={"item_7_mdna": {"uncertainty_term_density": 10.0}},
        language_deltas={"item_1a_risk_factors": {"uncertainty_language_delta": 1.0}},
        extraction_confs={"item_1a_risk_factors": 0.9, "item_7_mdna": 0.5},
    )
    filtered = filter_metrics_result(metrics, {"item_1a_risk_factors"})
    assert set(filtered.section_metrics) == {"item_1a_risk_factors"}
    assert set(filtered.section_diffs) == {"item_1a_risk_factors"}
    assert set(filtered.section_flags) == {"item_1a_risk_factors"}
    assert filtered.section_densities == {}
    assert set(filtered.language_deltas) == {"item_1a_risk_factors"}
    assert filtered.extraction_confs == {"item_1a_risk_factors": 0.9}


def test_filter_metrics_result_scopes_extraction_metadata():
    import hashlib

    from disclosure_alpha.pipeline import compute_section_metrics, filter_metrics_result
    from disclosure_alpha.section_extractor import ExtractedSection
    from disclosure_alpha.version import PARSER_VERSION

    def _section(name: str, text: str, warnings: list[str] | None = None) -> ExtractedSection:
        cleaned = text.strip()
        return ExtractedSection(
            section_name=name,
            raw_text=cleaned,
            cleaned_text=cleaned,
            text_hash=hashlib.sha256(cleaned.encode()).hexdigest()[:16],
            word_count=len(cleaned.split()),
            sentence_count=1,
            extraction_confidence=0.9,
            extraction_method="test",
            parser_version=PARSER_VERSION,
            warnings=warnings or [],
        )

    text_1a = "We may face litigation and regulatory investigation. " * 20
    text_7 = "Revenue may decline amid margin pressure. " * 20
    sections = [
        _section("item_1a_risk_factors", text_1a),
        _section("item_7_mdna", text_7, ["short_section"]),
    ]
    metrics = compute_section_metrics(sections, form_type="10-K")
    assert metrics.required_sections_present
    assert "short_section" in metrics.extraction_warnings

    filtered = filter_metrics_result(
        metrics,
        {"item_1a_risk_factors"},
        form_type="10-K",
        sections=sections,
    )
    assert filtered.extraction_confs == {"item_1a_risk_factors": 0.9}
    assert "short_section" not in filtered.extraction_warnings
    assert not filtered.required_sections_present
    assert "missing_required_section" in filtered.extraction_warnings


def test_filter_sections():
    from disclosure_alpha.pipeline import extract_sections_from_html, filter_sections
    from html_fixtures import minimal_10k_html

    sections = extract_sections_from_html(minimal_10k_html(), "10-K")
    filtered = filter_sections(sections, {"item_1a_risk_factors"})
    assert len(filtered) == 1
    assert filtered[0].section_name == "item_1a_risk_factors"


def test_metrics_dict_preserves_none():
    from types import SimpleNamespace

    from disclosure_alpha.pipeline import _metrics_dict

    metrics = SimpleNamespace(
        negative_word_ratio=None,
        uncertainty_word_ratio=0.05,
        litigious_word_ratio=None,
        modal_word_ratio=0.0,
        constraining_word_ratio=0.02,
        boilerplate_phrase_ratio=None,
        numeric_specificity_score=0.4,
        company_specificity_score=None,
        readability_score=None,
    )
    result = _metrics_dict(metrics)
    assert result["negative_word_ratio"] is None
    assert result["uncertainty_word_ratio"] == 0.05
    assert result["litigious_word_ratio"] is None
    assert result["modal_word_ratio"] == 0.0
    assert result["weak_modal_word_ratio"] is None
    assert result["readability_score"] is None
    assert result["numeric_specificity_score"] == 0.4


def test_compute_section_metrics_item_1a_flags():
    from disclosure_alpha.pipeline import compute_section_metrics, extract_sections_from_html
    from html_fixtures import minimal_10k_html

    sections = extract_sections_from_html(minimal_10k_html(), "10-K")
    metrics = compute_section_metrics(sections, form_type="10-K")
    assert "item_1a_risk_factors" in metrics.section_metrics
    assert "negative_word_ratio" in metrics.section_metrics["item_1a_risk_factors"]
    assert "investigation_flag" in metrics.section_flags["item_1a_risk_factors"]


def test_compute_section_metrics_extraction_metadata():
    from disclosure_alpha.pipeline import (
        compute_section_metrics,
        extract_sections_from_html,
        score_for_model,
    )
    from html_fixtures import minimal_10k_html

    html = (
        "<html><body><p>Item 7. Management's Discussion</p>"
        "<p>Only MDNA here without Item 1A.</p></body></html>"
    )
    sections = extract_sections_from_html(html, "10-K")
    metrics = compute_section_metrics(sections, form_type="10-K")
    assert not metrics.required_sections_present
    assert "missing_required_section" in metrics.extraction_warnings
    penalized = score_for_model(metrics).confidence_score

    clean_sections = extract_sections_from_html(minimal_10k_html(), "10-K")
    clean_metrics = compute_section_metrics(clean_sections, form_type="10-K")
    assert clean_metrics.required_sections_present
    clean = score_for_model(clean_metrics).confidence_score
    assert penalized < clean


def test_compute_section_metrics_aggregates_section_warnings():
    import hashlib

    from disclosure_alpha.pipeline import compute_section_metrics, score_for_model
    from disclosure_alpha.section_extractor import ExtractedSection
    from disclosure_alpha.version import PARSER_VERSION

    def _section(name: str, text: str, warnings: list[str] | None = None) -> ExtractedSection:
        cleaned = text.strip()
        return ExtractedSection(
            section_name=name,
            raw_text=cleaned,
            cleaned_text=cleaned,
            text_hash=hashlib.sha256(cleaned.encode()).hexdigest()[:16],
            word_count=len(cleaned.split()),
            sentence_count=1,
            extraction_confidence=0.9,
            extraction_method="test",
            parser_version=PARSER_VERSION,
            warnings=warnings or [],
        )

    text_1a = "We may face litigation and regulatory investigation. " * 20
    text_7 = "Revenue may decline amid margin pressure and liquidity constraints. " * 20
    warned = compute_section_metrics(
        [
            _section("item_1a_risk_factors", text_1a, ["short_section"]),
            _section("item_7_mdna", text_7),
        ],
        form_type="10-K",
    )
    assert "short_section" in warned.extraction_warnings
    warned_score = score_for_model(warned).confidence_score

    clean = compute_section_metrics(
        [_section("item_1a_risk_factors", text_1a), _section("item_7_mdna", text_7)],
        form_type="10-K",
    )
    assert "short_section" not in clean.extraction_warnings
    clean_score = score_for_model(clean).confidence_score
    assert warned_score < clean_score


def test_sec_parser_unavailable_lowers_confidence():
    import hashlib

    from disclosure_alpha.pipeline import compute_section_metrics, score_for_model
    from disclosure_alpha.section_extractor import ExtractedSection
    from disclosure_alpha.version import PARSER_VERSION

    def _section(name: str, text: str, warnings: list[str] | None = None) -> ExtractedSection:
        cleaned = text.strip()
        return ExtractedSection(
            section_name=name,
            raw_text=cleaned,
            cleaned_text=cleaned,
            text_hash=hashlib.sha256(cleaned.encode()).hexdigest()[:16],
            word_count=len(cleaned.split()),
            sentence_count=1,
            extraction_confidence=0.9,
            extraction_method="test",
            parser_version=PARSER_VERSION,
            warnings=warnings or [],
        )

    text_1a = "We may face litigation and regulatory investigation. " * 20
    text_7 = "Revenue may decline amid margin pressure and liquidity constraints. " * 20
    warned = compute_section_metrics(
        [
            _section("item_1a_risk_factors", text_1a, ["sec_parser_unavailable"]),
            _section("item_7_mdna", text_7),
        ],
        form_type="10-K",
    )
    assert "sec_parser_unavailable" in warned.extraction_warnings
    warned_score = score_for_model(warned).confidence_score

    clean = compute_section_metrics(
        [_section("item_1a_risk_factors", text_1a), _section("item_7_mdna", text_7)],
        form_type="10-K",
    )
    clean_score = score_for_model(clean).confidence_score
    assert warned_score < clean_score


def test_score_filing_html_includes_confidence_details():
    from html_fixtures import minimal_10k_html

    result = score_filing_html(minimal_10k_html(), "10-K")
    details = result.scores.confidence_details
    assert details is not None
    assert "base" in details
    assert "penalties" in details
    assert "confidence_details" in result.to_dict()["scores"]


def test_score_panel_tickers_handles_expected_errors(monkeypatch):
    from disclosure_alpha.edgar.types import FilingNotFoundError
    from disclosure_alpha.pipeline import score_panel_tickers

    ok_html = (
        "<html><body><p>Item 1A. Risk Factors</p>"
        "<p>We may face litigation.</p></body></html>"
    )
    good = score_filing_html(ok_html, "10-K")

    def fake_score(ticker, fiscal_year, **kwargs):
        if ticker == "BAD":
            raise FilingNotFoundError("No 10-K for BAD FY2025")
        result = good
        result.filing = {"ticker": ticker, "fiscal_year": fiscal_year}
        return result

    monkeypatch.setattr("disclosure_alpha.pipeline.score_filing_ticker", fake_score)
    batch = score_panel_tickers(["GOOD", "BAD", "GOOD2"], 2025)
    assert batch.summary == {"ok": 2, "failed": 1}
    by_ticker = {r.ticker: r for r in batch.results}
    assert by_ticker["GOOD"].status == "ok"
    assert by_ticker["BAD"].status == "error"
    assert "BAD" in by_ticker["BAD"].error
    assert by_ticker["GOOD2"].status == "ok"


def test_score_panel_tickers_propagates_unexpected_errors(monkeypatch):
    from disclosure_alpha.pipeline import score_panel_tickers

    def fake_score(ticker, fiscal_year, **kwargs):
        raise RuntimeError("unexpected bug")

    monkeypatch.setattr("disclosure_alpha.pipeline.score_filing_ticker", fake_score)
    with pytest.raises(RuntimeError, match="unexpected bug"):
        score_panel_tickers(["AAPL"], 2025)
