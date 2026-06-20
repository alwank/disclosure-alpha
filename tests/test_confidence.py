from disclosure_alpha.confidence import compute_overall_confidence


def test_confidence_empty_extraction_uses_coverage_only():
    assert compute_overall_confidence(
        extraction_confidences=[],
        llm_confidences=[],
        coverage_ratio=0.0,
    ) == 0.0


def test_confidence_averages_extraction_and_coverage():
    score = compute_overall_confidence(
        extraction_confidences=[0.8, 0.6],
        llm_confidences=[],
        coverage_ratio=1.0,
        diff_confidence=0.9,
    )
    assert score == round((0.7 + 1.0 + 0.9) / 3, 4)


def test_confidence_clamps_to_one():
    score = compute_overall_confidence(
        extraction_confidences=[1.0],
        llm_confidences=[1.0],
        coverage_ratio=1.0,
        diff_confidence=1.0,
    )
    assert score == 1.0
