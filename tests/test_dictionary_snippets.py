import json
from pathlib import Path

import pytest

from disclosure_alpha.diff_engine import extract_topics, compute_section_diff
from disclosure_alpha.dictionaries import FLAG_PATTERNS, FLAG_SECTION_SCOPE
from disclosure_alpha.text_matching import topic_intensity
from disclosure_alpha.dictionaries import SEVERITY_WORDS, TOPIC_KEYWORDS
from disclosure_alpha.text_metrics import (
    SectionTextInput,
    compute_density_metrics,
    compute_text_metrics,
    detect_section_flags,
)

SNIPPETS = json.loads(
    (Path(__file__).parent / "fixtures" / "dictionary_near_miss_snippets.json").read_text()
)

FLAG_TRIGGER_TEXT = {
    "material_weakness_flag": "material weakness in internal control over financial reporting",
    "significant_deficiency_flag": "significant deficiency in internal controls",
    "ineffective_controls_flag": "disclosure controls and procedures were ineffective",
    "restatement_flag": "we announced a restatement of prior results",
    "non_reliance_flag": "previously issued financial statements should no longer be relied upon",
    "auditor_change_flag": "change in certifying accountant",
    "investigation_flag": "SEC opened an investigation",
    "settlement_flag": "entered into a consent decree",
    "material_legal_proceeding_flag": "material legal proceeding pending",
    "going_concern_flag": "substantial doubt about our ability to continue as a going concern",
    "covenant_breach_flag": "event of default under our credit agreement",
    "guidance_withdrawal_flag": "we are withdrawing guidance",
    "cybersecurity_incident_flag": "material cybersecurity incident occurred",
}

FLAG_IN_SCOPE = {
    "material_weakness_flag": "item_9a_controls",
    "significant_deficiency_flag": "item_9a_controls",
    "ineffective_controls_flag": "item_9a_controls",
    "restatement_flag": "item_9a_controls",
    "non_reliance_flag": "item_9a_controls",
    "auditor_change_flag": "item_9a_controls",
    "investigation_flag": "item_1a_risk_factors",
    "settlement_flag": "item_3_legal_proceedings",
    "material_legal_proceeding_flag": "item_1_legal_proceedings",
    "going_concern_flag": "item_7_mdna",
    "covenant_breach_flag": "item_7_mdna",
    "guidance_withdrawal_flag": "item_2_02",
    "cybersecurity_incident_flag": "item_1_05",
}

OUT_OF_SCOPE_SECTION = "item_9a_controls"


@pytest.mark.parametrize("snippet", SNIPPETS, ids=lambda s: s.get("notes", s["text"][:40]))
def test_dictionary_snippet_fixture(snippet):
    section = snippet["section"]
    text = snippet["text"]
    flags = detect_section_flags(text, section)

    for flag_name, expected in snippet.get("expected_flags", {}).items():
        assert flags[flag_name] is expected, f"{flag_name} for {snippet.get('notes')}"

    if "expected_topics" in snippet:
        topics = extract_topics(text)
        expected = set(snippet["expected_topics"])
        assert expected <= topics, f"missing topics {expected - topics} for {snippet.get('notes')}"
        if not expected:
            assert not topics, f"unexpected topics {topics} for {snippet.get('notes')}"

    if metrics := snippet.get("expected_metrics"):
        result = compute_text_metrics(SectionTextInput(section, text))
        for key, val in metrics.items():
            if key.endswith("_gt"):
                field = key[:-3]
                assert getattr(result, field) > val
            elif key.endswith("_eq"):
                field = key[:-3]
                assert getattr(result, field) == val
            elif key.endswith("_lte"):
                field = key[:-4]
                assert getattr(result, field) <= val

    if density := snippet.get("expected_density"):
        densities = compute_density_metrics(text, section)
        for key, val in density.items():
            if key.endswith("_gt"):
                assert densities[key[:-3]] > val
            elif key.endswith("_eq"):
                assert densities[key[:-3]] == val


@pytest.mark.parametrize("flag_name", FLAG_PATTERNS.keys())
def test_flag_section_scope_in_scope(flag_name):
    section = FLAG_IN_SCOPE[flag_name]
    text = FLAG_TRIGGER_TEXT[flag_name]
    assert detect_section_flags(text, section)[flag_name] is True


@pytest.mark.parametrize("flag_name", FLAG_PATTERNS.keys())
def test_flag_section_scope_out_of_scope(flag_name):
    section = OUT_OF_SCOPE_SECTION
    if section in FLAG_SECTION_SCOPE[flag_name]:
        pytest.skip(f"{flag_name} includes {section} in scope")
    text = FLAG_TRIGGER_TEXT[flag_name]
    assert detect_section_flags(text, section)[flag_name] is False


TOKEN_CASES = [
    ("negative", "impairment and fraud losses occurred", "preimpairment review completed", "negative_word_ratio"),
    ("uncertainty", "contingencies remain unresolved and pending", "estimates are prepared routinely", "uncertainty_word_ratio"),
    ("litigious", "plaintiff filed an antitrust appeal", "reinvestigation completed internally", "litigious_word_ratio"),
    ("constraining", "collateral liens restrict refinancing", "compliance training is mandatory", "constraining_word_ratio"),
    ("weak_modal", "we may possibly expand", "tomorrow we launch", "modal_word_ratio"),
    ("moderate_modal", "we expect and believe growth", "actual results reported", "modal_word_ratio"),
    ("strong_modal", "we must comply and shall report", "quarter ended march", "modal_word_ratio"),
]


@pytest.mark.parametrize("category,pos,near,mfield", TOKEN_CASES)
def test_token_category_boundaries(category, pos, near, mfield):
    pos_result = compute_text_metrics(SectionTextInput("item_1a_risk_factors", pos))
    near_result = compute_text_metrics(SectionTextInput("item_1a_risk_factors", near))
    assert getattr(pos_result, mfield) > 0, category
    if category == "litigious" and "reinvestigation" in near:
        assert getattr(near_result, mfield) == 0.0
    elif category == "uncertainty" and "estimates" in near:
        assert getattr(near_result, mfield) == 0.0


def test_boilerplate_once_per_sentence_dedup():
    repeated = "There can be no assurance. There can be no assurance."
    result = compute_text_metrics(SectionTextInput("item_1a_risk_factors", repeated))
    assert result.boilerplate_phrase_ratio == 1.0
    single = "There can be no assurance there can be no assurance."
    single_result = compute_text_metrics(SectionTextInput("item_1a_risk_factors", single))
    assert single_result.boilerplate_phrase_ratio < 2.0


def test_uncertainty_monotonicity():
    base = compute_text_metrics(
        SectionTextInput("item_1a_risk_factors", "We operate globally.")
    )
    enriched = compute_text_metrics(
        SectionTextInput(
            "item_1a_risk_factors",
            "We operate globally. Outcomes may be uncertain and volatile.",
        )
    )
    assert enriched.uncertainty_word_ratio > base.uncertainty_word_ratio
    assert enriched.negative_word_ratio == base.negative_word_ratio


def test_v2_flag_phrases():
    assert detect_section_flags(
        "Material weaknesses in internal control over financial reporting were noted.",
        "item_9a_controls",
    )["material_weakness_flag"]
    assert detect_section_flags(
        "The company no longer expects prior revenue guidance.",
        "item_2_02",
    )["guidance_withdrawal_flag"]
    assert detect_section_flags(
        "Systems outage and incident response continued for days.",
        "item_1_05",
    )["cybersecurity_incident_flag"]


def test_topic_severity_window():
    distant = (
        "Information security policies are reviewed annually. "
        "Critical risks are disclosed elsewhere in this filing."
    )
    adjacent = "A severe cybersecurity breach materially affected operations."
    distant_intensity = topic_intensity(
        distant, "cybersecurity", TOPIC_KEYWORDS, SEVERITY_WORDS
    )
    adjacent_intensity = topic_intensity(
        adjacent, "cybersecurity", TOPIC_KEYWORDS, SEVERITY_WORDS
    )
    assert adjacent_intensity > distant_intensity
    assert distant_intensity == 0.0


def test_topic_competition_boundary():
    assert "competition" in extract_topics("Intense competition may reduce share.")
    assert "competition" not in extract_topics("We operate in competitive markets.")


def test_severity_intensifies_topic_diff():
    prior = "We face cybersecurity risk."
    current = "We face a severe material cybersecurity breach."
    diff = compute_section_diff(current_text=current, prior_text=prior)
    assert "cybersecurity" in diff.new_topics or "cybersecurity" in diff.intensified_topics
