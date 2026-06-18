def compute_overall_confidence(
    *,
    extraction_confidences: list[float],
    llm_confidences: list[float],
    coverage_ratio: float,
    diff_confidence: float | None = None,
) -> float:
    parts: list[float] = []
    if extraction_confidences:
        parts.append(sum(extraction_confidences) / len(extraction_confidences))
    if llm_confidences:
        parts.append(sum(llm_confidences) / len(llm_confidences))
    parts.append(coverage_ratio)
    if diff_confidence is not None:
        parts.append(diff_confidence)
    if not parts:
        return 0.3
    return round(max(0.0, min(1.0, sum(parts) / len(parts))), 4)
