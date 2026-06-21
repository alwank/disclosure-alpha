from disclosure_alpha.text_metrics import (
    SectionTextInput,
    compute_density_metrics,
    compute_text_metrics,
    detect_section_flags,
)
from disclosure_alpha.version import DICTIONARY_VERSION
from disclosure_alpha.dictionaries import (
    MODAL_WORDS,
    MODERATE_MODAL_WORDS,
    STRONG_MODAL_WORDS,
    WEAK_MODAL_WORDS,
    sections_for_form_type,
)


def test_empty_text():
    result = compute_text_metrics(SectionTextInput("item_1a_risk_factors", ""))
    assert result.word_count == 0
    assert result.sentence_count == 0
    assert result.uncertainty_word_ratio == 0.0


def test_uncertainty_and_litigious_ratios():
    text = (
        "We may face litigation and regulatory investigation. "
        "Results could be uncertain and volatile."
    )
    result = compute_text_metrics(SectionTextInput("item_1a_risk_factors", text))
    assert result.uncertainty_word_ratio > 0
    assert result.litigious_word_ratio > 0


def test_enriched_finance_word_categories():
    text = (
        "Fraudulent misstatements caused insolvency and outages. "
        "Contingencies remain unresolved pending an antitrust arbitration appeal. "
        "Debt maturities and liens restricted pledged collateral."
    )
    result = compute_text_metrics(SectionTextInput("item_1a_risk_factors", text))
    assert result.negative_word_ratio > 0
    assert result.uncertainty_word_ratio > 0
    assert result.litigious_word_ratio > 0
    assert result.constraining_word_ratio > 0


def test_modal_split_preserves_compatibility():
    assert DICTIONARY_VERSION == "built_in_dictionaries_v2"
    assert WEAK_MODAL_WORDS | MODERATE_MODAL_WORDS | STRONG_MODAL_WORDS == MODAL_WORDS
    text = "We may refinance and will be obligated to comply with covenants."
    result = compute_text_metrics(SectionTextInput("item_7_mdna", text))
    assert result.modal_word_ratio > 0


def test_boilerplate_ratio():
    text = "There can be no assurance that results may materially adversely affect our business."
    result = compute_text_metrics(SectionTextInput("item_1a_risk_factors", text))
    assert result.boilerplate_phrase_ratio > 0


def test_expanded_safe_harbor_boilerplate_ratio():
    text = "Actual results could differ materially. You should not place undue reliance."
    result = compute_text_metrics(SectionTextInput("item_1a_risk_factors", text))
    assert result.boilerplate_phrase_ratio > 0


def test_expanded_boilerplate_phrase_boundary():
    result = compute_text_metrics(
        SectionTextInput(
            "item_1a_risk_factors",
            "These risks are not exhaustive and could materially and adversely affect results.",
        )
    )
    near_miss = compute_text_metrics(
        SectionTextInput("item_1a_risk_factors", "The review was not exhaustively performed.")
    )
    assert result.boilerplate_phrase_ratio > 0
    assert near_miss.boilerplate_phrase_ratio == 0.0


def test_risk_heading_terms_do_not_inflate_negative_ratio():
    text = "Risk Factors. We disclose risks related to our business."
    result = compute_text_metrics(SectionTextInput("item_1a_risk_factors", text))
    assert result.negative_word_ratio == 0.0


def test_numeric_specificity():
    text = "Revenue was $10.5 billion in 2024 across 3 regions with 15% growth."
    result = compute_text_metrics(SectionTextInput("item_7_mdna", text))
    assert result.numeric_specificity_score > 0


def test_internal_controls_flags():
    text = "We identified a material weakness in internal control over financial reporting."
    flags = detect_section_flags(text, "item_9a_controls")
    assert flags["material_weakness_flag"] is True
    assert flags["going_concern_flag"] is False


def test_liquidity_flags():
    text = "There is substantial doubt about our ability to continue as a going concern."
    flags = detect_section_flags(text, "item_7_mdna")
    assert flags["going_concern_flag"] is True


def test_legal_flags():
    text = "The SEC opened an investigation and issued a subpoena."
    flags = detect_section_flags(text, "item_1a_risk_factors")
    assert flags["investigation_flag"] is True


def test_expanded_legal_and_control_flags():
    legal = "The Company received a Wells notice and entered into a consent order."
    flags = detect_section_flags(legal, "item_3_legal_proceedings")
    assert flags["investigation_flag"] is True
    assert flags["settlement_flag"] is True

    controls = "Management concluded that our internal control over financial reporting was ineffective."
    assert detect_section_flags(controls, "item_9a_controls")["ineffective_controls_flag"] is True


def test_guidance_withdrawal_flag_mdna_only():
    text = "We withdraw our guidance for the remainder of the fiscal year."
    assert detect_section_flags(text, "item_7_mdna")["guidance_withdrawal_flag"] is True
    assert detect_section_flags(text, "item_1a_risk_factors")["guidance_withdrawal_flag"] is False
    assert detect_section_flags(text, "item_2_02")["guidance_withdrawal_flag"] is True


def test_expanded_guidance_and_covenant_flags():
    guidance = "The company is withdrawing guidance and is unable to provide guidance."
    assert detect_section_flags(guidance, "item_2_02")["guidance_withdrawal_flag"] is True

    covenant = "We received a waiver from lenders after an event of default."
    assert detect_section_flags(covenant, "item_7_mdna")["covenant_breach_flag"] is True
    assert detect_section_flags("Users can restore default settings.", "item_7_mdna")[
        "covenant_breach_flag"
    ] is False


def test_cybersecurity_incident_flag_scoped_to_cyber_sections():
    text = "We determined that the ransomware event was a material cybersecurity incident."
    assert detect_section_flags(text, "item_1_05")["cybersecurity_incident_flag"] is True
    assert detect_section_flags(text, "item_7_mdna")["cybersecurity_incident_flag"] is False


def test_expanded_cybersecurity_incident_flag_without_governance_false_positive():
    incident = "The ransomware attack involved unauthorized access and data exfiltration."
    governance = "Our cybersecurity program includes board oversight and annual training."
    assert detect_section_flags(incident, "item_1_05")["cybersecurity_incident_flag"] is True
    assert detect_section_flags(governance, "item_1c_cybersecurity")[
        "cybersecurity_incident_flag"
    ] is False


def test_investigation_flag_word_boundary():
    assert detect_section_flags("SEC opened an investigation.", "item_1a_risk_factors")[
        "investigation_flag"
    ] is True
    assert detect_section_flags("We completed a reinvestigation of controls.", "item_1a_risk_factors")[
        "investigation_flag"
    ] is False


def test_restatement_flag_word_boundary():
    assert detect_section_flags("We announced a restatement of prior results.", "item_1a_risk_factors")[
        "restatement_flag"
    ] is True
    assert detect_section_flags("No prestatement adjustments were required.", "item_9a_controls")[
        "restatement_flag"
    ] is False


def test_mdna_density_metrics():
    text = (
        "Demand declined amid margin pressure. We may face liquidity constraint "
        "and debt maturity pressure if conditions worsen."
    )
    densities = compute_density_metrics(text, "item_7_mdna")
    assert densities["demand_softness_density"] > 0
    assert densities["margin_pressure_density"] > 0
    assert densities["uncertainty_term_density"] > 0
    assert all(0 <= v <= 100 for v in densities.values())


def test_density_zero_outside_mdna():
    densities = compute_density_metrics("demand declined", "item_1a_risk_factors")
    assert all(v == 0.0 for v in densities.values())


def test_expanded_mdna_density_phrases():
    text = (
        "Inflationary pressures caused lower gross margins. "
        "Cash shortfall risk increased cash requirements."
    )
    densities = compute_density_metrics(text, "item_7_mdna")
    assert densities["margin_pressure_density"] > 0
    assert densities["liquidity_constraint_density"] > 0


def test_enriched_mdna_density_phrases():
    text = (
        "Known uncertainties include customer destocking and lower volumes. "
        "Gross margin decreased due to higher input costs. "
        "We may need to raise capital because of negative working capital."
    )
    densities = compute_density_metrics(text, "item_7_mdna")
    assert densities["uncertainty_term_density"] > 0
    assert densities["demand_softness_density"] > 0
    assert densities["margin_pressure_density"] > 0
    assert densities["liquidity_constraint_density"] > 0


def test_8k_item_1_05_supported():
    sections = sections_for_form_type("8-K")
    assert "item_1_05" in sections
