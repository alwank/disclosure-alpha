"""EDGAR ingestion and extraction quality gates for L2."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

from disclosure_alpha.validation.types import CorpusRow

GateStatus = Literal["pass", "fail"]


@dataclass
class EdgarGateResult:
    name: str
    status: GateStatus
    value: float | int | None
    threshold: float | int
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EdgarGatesConfig:
    min_fetch_rate: float = 0.90
    min_analysis_rate: float = 0.85
    min_filter_retention: float = 0.85
    min_median_confidence: float = 0.75
    min_analysis_n: int = 80


def _median_confidence(rows: list[CorpusRow]) -> float | None:
    confs = [r.extraction_confidence for r in rows if r.extraction_confidence is not None]
    if not confs:
        return None
    confs.sort()
    mid = len(confs) // 2
    if len(confs) % 2:
        return confs[mid]
    return (confs[mid - 1] + confs[mid]) / 2


def _gate(
    name: str,
    value: float | int | None,
    threshold: float | int,
    *,
    higher_is_better: bool = True,
) -> EdgarGateResult:
    if value is None:
        return EdgarGateResult(name=name, status="fail", value=None, threshold=threshold, message="missing value")
    ok = value >= threshold if higher_is_better else value <= threshold
    return EdgarGateResult(
        name=name,
        status="pass" if ok else "fail",
        value=value,
        threshold=threshold,
    )


def evaluate_edgar_gates(
    corpus_meta: dict[str, Any],
    analysis_rows: list[CorpusRow],
    *,
    config: EdgarGatesConfig | None = None,
    manifest: dict[str, Any] | None = None,
) -> tuple[dict[str, EdgarGateResult], bool, dict[str, Any]]:
    cfg = config or EdgarGatesConfig()
    universe_expected = int(corpus_meta.get("universe_expected") or 0)
    n_input = int(corpus_meta.get("n_input") or 0)
    n_after = int(corpus_meta.get("n_after_filters") or len(analysis_rows))

    fetch_rate = (n_input / universe_expected) if universe_expected else None
    analysis_rate = (n_after / universe_expected) if universe_expected else None
    filter_retention = (n_after / n_input) if n_input else None
    median_conf = _median_confidence(analysis_rows)

    gates = {
        "E1_fetch_rate": _gate("E1_fetch_rate", fetch_rate, cfg.min_fetch_rate),
        "E2_analysis_rate": _gate("E2_analysis_rate", analysis_rate, cfg.min_analysis_rate),
        "E3_filter_retention": _gate("E3_filter_retention", filter_retention, cfg.min_filter_retention),
        "E4_median_confidence": _gate("E4_median_confidence", median_conf, cfg.min_median_confidence),
        "E5_min_analysis_n": _gate("E5_min_analysis_n", n_after, cfg.min_analysis_n),
    }

    extras: dict[str, Any] = {}
    if manifest:
        failures = manifest.get("failures") or []
        extras["manifest_failures"] = len(failures)
        extras["manifest_failure_reasons"] = _count_reasons(failures)

    edgar_pass = all(g.status == "pass" for g in gates.values())
    return gates, edgar_pass, extras


def _count_reasons(failures: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in failures:
        reason = item.get("reason", "unknown")
        counts[reason] = counts.get(reason, 0) + 1
    return counts
