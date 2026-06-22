from dataclasses import dataclass, field


@dataclass
class ConfidenceInput:
    extraction_confidences: list[float]
    extraction_warnings: list[str] = field(default_factory=list)
    coverage_ratio: float = 0.0
    required_sections_present: bool = True
    diff_confidence: float | None = None
    has_prior: bool = True


_WARNING_PENALTIES: dict[str, float] = {
    "short_section": 0.08,
    "extraction_suspect": 0.12,
    "last_resort_extraction": 0.12,
}


def compute_confidence_detailed(
    inp: ConfidenceInput,
) -> tuple[float, dict[str, object]]:
    parts: list[float] = []
    if inp.extraction_confidences:
        parts.append(sum(inp.extraction_confidences) / len(inp.extraction_confidences))
    parts.append(inp.coverage_ratio)
    if inp.diff_confidence is not None:
        parts.append(inp.diff_confidence)
    base = sum(parts) / len(parts) if parts else 0.3

    penalties: list[tuple[str, float]] = []
    if not inp.required_sections_present:
        penalties.append(("missing_required_section", 0.25))
    for warning in inp.extraction_warnings:
        pen = _WARNING_PENALTIES.get(warning)
        if pen is not None:
            penalties.append((warning, pen))
    if not inp.has_prior:
        penalties.append(("no_prior_filing", 0.10))
    if inp.coverage_ratio < 0.75:
        gap = 0.75 - inp.coverage_ratio
        penalties.append(("low_coverage", min(0.20, gap * 0.4)))

    total_penalty = sum(p for _, p in penalties)
    score = round(max(0.0, min(1.0, base - total_penalty)), 4)
    details: dict[str, object] = {
        "base": round(base, 4),
        "penalties": {name: pen for name, pen in penalties},
        "total_penalty": round(total_penalty, 4),
    }
    return score, details


def compute_overall_confidence(
    *,
    extraction_confidences: list[float],
    coverage_ratio: float,
    diff_confidence: float | None = None,
    extraction_warnings: list[str] | None = None,
    required_sections_present: bool = True,
    has_prior: bool = True,
) -> float:
    """Backward-compatible wrapper; delegates to detailed confidence model."""
    score, _ = compute_confidence_detailed(
        ConfidenceInput(
            extraction_confidences=extraction_confidences,
            extraction_warnings=extraction_warnings or [],
            coverage_ratio=coverage_ratio,
            required_sections_present=required_sections_present,
            diff_confidence=diff_confidence,
            has_prior=has_prior,
        )
    )
    return score
