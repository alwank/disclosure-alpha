from disclosure_alpha.confidence import compute_overall_confidence


def test_confidence_empty_extraction_uses_coverage_only():
    assert compute_overall_confidence(
        extraction_confidences=[],
        coverage_ratio=0.0,
    ) == 0.0


def test_confidence_averages_extraction_and_coverage():
    score = compute_overall_confidence(
        extraction_confidences=[0.8, 0.6],
        coverage_ratio=1.0,
        diff_confidence=0.9,
    )
    assert score == round((0.7 + 1.0 + 0.9) / 3, 4)


def test_confidence_clamps_to_one():
    score = compute_overall_confidence(
        extraction_confidences=[1.0],
        coverage_ratio=1.0,
        diff_confidence=1.0,
    )
    assert score == 1.0


def test_confidence_penalizes_warnings_and_missing_sections():
    from disclosure_alpha.confidence import ConfidenceInput, compute_confidence_detailed

    clean, _ = compute_confidence_detailed(
        ConfidenceInput(
            extraction_confidences=[0.8],
            coverage_ratio=1.0,
        )
    )
    noisy, details = compute_confidence_detailed(
        ConfidenceInput(
            extraction_confidences=[0.8],
            extraction_warnings=["short_section", "extraction_suspect"],
            coverage_ratio=1.0,
            required_sections_present=False,
            has_prior=False,
        )
    )
    assert noisy < clean
    assert "missing_required_section" in details["penalties"]
    assert "no_prior_filing" in details["penalties"]


def test_confidence_low_coverage_nonlinear_penalty():
    from disclosure_alpha.confidence import ConfidenceInput, compute_confidence_detailed

    high, _ = compute_confidence_detailed(
        ConfidenceInput(extraction_confidences=[0.9], coverage_ratio=0.9)
    )
    low, _ = compute_confidence_detailed(
        ConfidenceInput(extraction_confidences=[0.9], coverage_ratio=0.4)
    )
    assert low < high
