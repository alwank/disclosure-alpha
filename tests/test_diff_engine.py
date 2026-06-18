import os

os.environ["EMBEDDING_BACKEND"] = "tfidf"

from disclosure_alpha.diff_engine import compute_section_diff


def test_identical_text_low_change():
    text = "We face regulatory litigation and supply chain risk."
    diff = compute_section_diff(current_text=text, prior_text=text)
    assert diff.disclosure_change_score is not None
    assert diff.disclosure_change_score < 30


def test_new_topic_higher_change():
    prior = "We operate in competitive markets."
    current = prior + " We face a new cybersecurity breach investigation and liquidity covenant risk."
    diff = compute_section_diff(current_text=current, prior_text=prior)
    assert diff.disclosure_change_score is not None
    assert diff.disclosure_change_score > 20
    assert diff.new_topics


def test_missing_prior_null_score():
    diff = compute_section_diff(current_text="some text", prior_text=None)
    assert diff.disclosure_change_score is None
    assert "prior" in diff.diff_summary.lower()


def test_language_deltas():
    prior = "We may face uncertain litigation risk."
    current = prior + " Additional regulatory investigation and covenant breach risk."
    diff = compute_section_diff(current_text=current, prior_text=prior)
    assert diff.language_deltas
    assert "uncertainty_language_delta" in diff.language_deltas
    assert diff.language_deltas["legal_language_delta"] >= 0


def test_combined_similarity_lexical_blend():
    prior = "We operate in competitive markets with stable demand."
    current = prior + " New cybersecurity litigation and covenant breach risk emerged."
    diff = compute_section_diff(current_text=current, prior_text=prior)
    assert diff.lexical_similarity is not None
    assert diff.semantic_similarity is not None
    combined = 0.6 * diff.semantic_similarity + 0.4 * diff.lexical_similarity
    expected = 40 * (1 - combined)
    assert diff.disclosure_change_score is not None
    assert diff.disclosure_change_score >= expected - 25
