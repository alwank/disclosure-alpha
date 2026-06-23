"""Section maps, metadata, and form-type helpers."""

TERM_PACK_METADATA = {
    "negative": {
        "source": "built_in_finance_curated",
        "match_type": "token",
        "consumer": ["negative_word_ratio", "risk_factor_intensity_score"],
        "license": "repo_safe_manual_curation",
    },
    "uncertainty": {
        "source": "built_in_finance_curated",
        "match_type": "token",
        "consumer": ["uncertainty_word_ratio", "mdna_uncertainty_score"],
        "license": "repo_safe_manual_curation",
    },
    "litigious": {
        "source": "built_in_finance_curated",
        "match_type": "token",
        "consumer": ["litigious_word_ratio", "legal_regulatory_risk_score"],
        "license": "repo_safe_manual_curation",
    },
    "legal_regulatory": {
        "source": "sec_pcaob_fasb_phrase_curated",
        "match_type": "phrase",
        "consumer": ["legal_regulatory_phrase_ratio"],
        "license": "repo_safe_manual_curation",
    },
    "constraining": {
        "source": "built_in_finance_curated",
        "match_type": "token",
        "consumer": ["constraining_word_ratio", "liquidity_stress_score"],
        "license": "repo_safe_manual_curation",
    },
    "modal": {
        "source": "built_in_finance_curated",
        "match_type": "token",
        "consumer": [
            "modal_word_ratio",
            "weak_modal_word_ratio",
            "moderate_modal_word_ratio",
            "strong_modal_word_ratio",
            "mdna_uncertainty_score",
        ],
        "license": "repo_safe_manual_curation",
    },
    "boilerplate": {
        "source": "built_in_finance_curated",
        "match_type": "phrase",
        "consumer": ["boilerplate_phrase_ratio", "boilerplate_risk_score"],
        "license": "repo_safe_manual_curation",
    },
    "topics": {
        "source": "built_in_finance_curated",
        "match_type": "phrase",
        "consumer": ["diff_engine.new_topics", "diff_engine.intensified_topics"],
        "license": "repo_safe_manual_curation",
    },
    "severity": {
        "source": "built_in_finance_curated",
        "match_type": "token",
        "consumer": ["diff_engine.topic_intensity"],
        "license": "repo_safe_manual_curation",
    },
    "flags": {
        "source": "sec_pcaob_fasb_phrase_curated",
        "match_type": "phrase",
        "consumer": ["section_flags", "component_flag_boosts"],
        "license": "repo_safe_manual_curation",
    },
    "mdna_density": {
        "source": "built_in_finance_curated",
        "match_type": "phrase",
        "consumer": [
            "uncertainty_term_density",
            "demand_softness_density",
            "margin_pressure_density",
            "liquidity_constraint_density",
        ],
        "license": "repo_safe_manual_curation",
    },
    "geography": {
        "source": "built_in_finance_curated",
        "match_type": "phrase",
        "consumer": ["company_specificity_score"],
        "license": "repo_safe_manual_curation",
    },
    "segment": {
        "source": "built_in_finance_curated",
        "match_type": "phrase",
        "consumer": ["company_specificity_score"],
        "license": "repo_safe_manual_curation",
    },
}

SUPPORTED_SECTIONS_10K = {
    # ponytail: [^a-z]{0,40} bridges "Item 1A, \"Risk Factors\"" and "1A.\n\nRisk Factors" TOC styles
    "item_1a_risk_factors": r"(?:item\s*)?1a\.?[^a-z]{0,40}risk\s*factors",
    "item_3_legal_proceedings": r"(?:item\s*)?3\.?[^a-z]{0,40}legal\s*proceedings",
    "item_7_mdna": r"(?:item\s*)?7\.?[^a-z]{0,40}management",
    "item_7a_market_risk": r"(?:item\s*)?7a\.?[^a-z]{0,40}quantitative",
    "item_9a_controls": r"(?:item\s*)?9a\.?[^a-z]{0,40}controls",
    "item_1c_cybersecurity": r"(?:item\s*)?1c\.?[^a-z]{0,40}cybersecurity",
}

SUPPORTED_SECTIONS_10Q = {
    "item_1a_risk_factors": r"item\s*1a\.?\s*risk\s*factors",
    "item_2_mdna": r"item\s*2\.?\s*management",
    "item_1_legal_proceedings": r"item\s*1\.?\s*legal\s*proceedings",
    "item_4_controls": r"item\s*4\.?\s*controls",
}

SUPPORTED_SECTIONS_8K = {
    "item_1_01": r"item\s*1\.01",
    "item_1_05": r"item\s*1\.05(?:[^a-z]{0,80}material\s*cybersecurity\s*incidents)?",
    "item_2_02": r"item\s*2\.02",
    "item_5_02": r"item\s*5\.02",
    "item_8_01": r"item\s*8\.01",
}

SUPPORTED_SECTIONS = SUPPORTED_SECTIONS_10K  # default backward compat

REQUIRED_SECTIONS = {
    "10-K": ["item_1a_risk_factors", "item_7_mdna"],
    "10-Q": ["item_1a_risk_factors", "item_2_mdna"],
    "8-K": ["item_2_02"],
}

SECTION_DISPLAY_NAMES = {
    "item_1a_risk_factors": "Item 1A Risk Factors",
    "item_3_legal_proceedings": "Item 3 Legal Proceedings",
    "item_7_mdna": "Item 7 Management's Discussion and Analysis",
    "item_7a_market_risk": "Item 7A Market Risk",
    "item_9a_controls": "Item 9A Controls and Procedures",
    "item_1c_cybersecurity": "Item 1C Cybersecurity",
    "item_2_mdna": "Item 2 MD&A",
    "item_1_legal_proceedings": "Item 1 Legal Proceedings",
    "item_4_controls": "Item 4 Controls and Procedures",
    "item_1_01": "Item 1.01 Entry into Material Agreement",
    "item_1_05": "Item 1.05 Material Cybersecurity Incidents",
    "item_2_02": "Item 2.02 Results of Operations",
    "item_5_02": "Item 5.02 Departure of Directors",
    "item_8_01": "Item 8.01 Other Events",
}

MVP_FORM_TYPES = frozenset({"10-K", "10-Q"})


def sections_for_form_type(form_type: str) -> dict[str, str]:
    base = form_type.replace("/A", "").replace("-A", "").upper()
    if base == "10-Q":
        return SUPPORTED_SECTIONS_10Q
    if base == "8-K":
        return SUPPORTED_SECTIONS_8K
    return SUPPORTED_SECTIONS_10K
