import os

os.environ["EMBEDDING_BACKEND"] = "tfidf"

from disclosure_alpha.diff_engine import compute_section_diff
from disclosure_alpha.text_matching import align_sentences, extract_numeric_tokens, split_sentences


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


def test_v2_fields_populated_with_prior():
    prior = "We operate in competitive markets with stable demand."
    current = prior + " New severe regulatory investigation and covenant breach risk emerged."
    diff = compute_section_diff(current_text=current, prior_text=prior)
    assert diff.disclosure_change_score_v2 is not None
    assert diff.added_sentence_count >= 1
    assert diff.diff_evidence
    assert "sentence_alignment" in diff.diff_evidence


def test_reorder_scores_lower_than_new_risk_on_v2():
    base = (
        "We face competition and regulatory risk. "
        "Supply chain disruption may affect results. "
        "Cybersecurity threats remain a concern."
    )
    reordered = ". ".join(reversed(split_sentences(base)))
    severe_addition = base + " A material cybersecurity breach investigation and liquidity covenant default occurred."
    reorder_diff = compute_section_diff(current_text=reordered, prior_text=base)
    severe_diff = compute_section_diff(current_text=severe_addition, prior_text=base)
    assert reorder_diff.disclosure_change_score_v2 is not None
    assert severe_diff.disclosure_change_score_v2 is not None
    assert severe_diff.disclosure_change_score_v2 > reorder_diff.disclosure_change_score_v2


def test_numeric_change_detection():
    prior = "Revenue was $100 million with 5% growth."
    current = "Revenue was $150 million with 12% growth."
    diff = compute_section_diff(current_text=current, prior_text=prior)
    assert diff.changed_numeric_count >= 1
    assert diff.diff_evidence.get("numeric_changes")


def test_align_sentences_added_removed():
    prior = ["We face competition.", "Demand may decline."]
    current = ["We face competition.", "A ransomware investigation began."]
    added, removed, matched = align_sentences(current, prior)
    assert len(matched) >= 1
    assert len(added) >= 1
    assert "ransomware" in " ".join(added).lower()


def test_extract_numeric_tokens():
    tokens = extract_numeric_tokens("Revenue rose 12% to $4.5 million in 2024.")
    assert any("12" in t or "pct:12" in t for t in tokens)
    assert any("4.5" in t for t in tokens)
