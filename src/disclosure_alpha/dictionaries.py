"""Built-in word lists for deterministic text metrics. Replaceable with licensed dictionaries."""

DICTIONARY_VERSION = "built_in_dictionaries_v1"

NEGATIVE_WORDS = frozenset(
    {
        "loss", "losses", "decline", "declined", "adverse", "adversely", "impairment",
        "deterioration", "weakness", "weak", "negative", "deficit", "shortfall",
        "downgrade", "failure", "failed", "harm", "damage", "breach", "default",
    }
)

UNCERTAINTY_WORDS = frozenset(
    {
        "may", "might", "could", "uncertain", "uncertainty", "volatility", "volatile",
        "unpredictable", "depend", "depends", "possible", "potentially",
    }
)

LITIGIOUS_WORDS = frozenset(
    {
        "litigation", "lawsuit", "investigation", "inquiry", "regulatory", "enforcement",
        "claim", "claims", "proceeding", "proceedings", "subpoena", "subpoenas",
        "settlement", "complaint", "penalty", "penalties", "plaintiff", "defendant",
    }
)

CONSTRAINING_WORDS = frozenset(
    {
        "covenant", "covenants", "restriction", "restrictions", "limitation", "limitations",
        "mandatory", "obligation", "obligations", "compliance", "constraint", "constraints",
        "default", "defaults", "breach", "breaches",
    }
)

MODAL_WORDS = frozenset(
    {
        "may", "could", "might", "should", "would", "expect", "expects", "intend",
        "intends", "believe", "believes",
    }
)

BOILERPLATE_PHRASES = [
    "actual results could differ materially",
    "could adversely affect our business",
    "may materially adversely affect",
    "we cannot assure you",
    "we cannot predict all such risk factors",
    "subject to risks and uncertainties",
    "you should not place undue reliance",
    "should not place undue reliance",
    "from time to time",
    "there can be no assurance",
]

GEOGRAPHY_TERMS = frozenset(
    {
        "americas", "europe", "asia", "china", "japan", "international", "domestic",
        "global", "region", "regions", "country", "countries",
    }
)

SEGMENT_TERMS = frozenset(
    {
        "segment", "segments", "division", "divisions", "business unit", "product line",
    }
)

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "legal/regulatory": [
        "litigation",
        "lawsuit",
        "regulatory enforcement",
        "regulatory investigation",
        "regulatory inquiry",
        "enforcement action",
        "investigation",
        "subpoena",
        "civil penalty",
        "settlement",
    ],
    "liquidity": [
        "liquidity",
        "cash shortfall",
        "cash burn",
        "cash requirements",
        "liquidity position",
        "refinancing",
        "covenant",
        "going concern",
        "working capital",
    ],
    "supply chain": [
        "supplier",
        "supply chain",
        "supply chain disruption",
        "supply chain disruptions",
        "sourcing",
        "vendor",
    ],
    "cybersecurity": [
        "cybersecurity",
        "cyber incident",
        "cybersecurity incident",
        "cybersecurity breach",
        "security incident",
        "security breach",
        "ransomware",
        "data breach",
    ],
    "customer concentration": ["major customer", "customer concentration", "largest customer"],
    "supplier concentration": ["sole supplier", "single supplier", "supplier concentration"],
    "macroeconomic": ["recession", "inflation", "macroeconomic", "economic downturn"],
    "interest rate": [
        "interest rate",
        "interest rates",
        "borrowing cost",
        "borrowing costs",
        "rate hikes",
        "variable-rate debt",
    ],
    "fx": [
        "foreign exchange",
        "foreign currency",
        "foreign currency fluctuations",
        "currency exchange",
        "exchange rate",
        "fx",
    ],
    "commodity": ["commodity", "commodities", "raw material", "raw material costs"],
    "competition": ["competitive", "competition", "competitor"],
    "product/platform": [
        "product defect",
        "product liability",
        "product launch delay",
        "platform outage",
        "technology failure",
    ],
    "operational": [
        "operational disruption",
        "manufacturing disruption",
        "production delay",
        "facility closure",
    ],
    "accounting/internal controls": [
        "internal control",
        "internal control over financial reporting",
        "material weakness",
        "restatement",
    ],
    "geopolitical": ["geopolitical", "sanctions", "tariff", "trade war"],
    "climate": ["climate", "carbon", "emissions", "sustainability"],
    "labor": ["labor shortage", "workforce reduction", "union", "strike", "strikes"],
}

SEVERITY_WORDS = frozenset(
    {"severe", "material", "significant", "substantial", "critical", "adverse", "major"}
)

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


def sections_for_form_type(form_type: str) -> dict[str, str]:
    base = form_type.replace("/A", "").replace("-A", "").upper()
    if base == "10-Q":
        return SUPPORTED_SECTIONS_10Q
    if base == "8-K":
        return SUPPORTED_SECTIONS_8K
    return SUPPORTED_SECTIONS_10K

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

# --- metrics v1.1: section flags and MD&A density packs ---

FLAG_PATTERNS: dict[str, list[str]] = {
    "material_weakness_flag": [
        "material weakness",
        "material weaknesses",
        "material weakness in internal control over financial reporting",
    ],
    "significant_deficiency_flag": ["significant deficiency", "significant deficiencies"],
    "ineffective_controls_flag": [
        "not effective",
        "ineffective internal control",
        "disclosure controls and procedures were not effective",
        "disclosure controls and procedures are not effective",
    ],
    "restatement_flag": ["restatement", "restated", "revision of previously issued"],
    "non_reliance_flag": ["should no longer be relied upon", "non-reliance"],
    "auditor_change_flag": ["change in certifying accountant", "resignation of our independent"],
    "investigation_flag": [
        "investigation",
        "subpoena",
        "inquiry by the sec",
        "regulatory inquiry",
        "regulatory investigation",
    ],
    "settlement_flag": ["settlement", "consent decree", "civil penalty"],
    "material_legal_proceeding_flag": ["material legal proceeding", "material litigation"],
    "going_concern_flag": [
        "going concern",
        "continue as a going concern",
        "substantial doubt about our ability",
    ],
    "covenant_breach_flag": [
        "covenant breach",
        "default under",
        "violation of covenants",
        "breach of covenant",
        "failed to comply with covenants",
    ],
    "guidance_withdrawal_flag": [
        "withdraw our guidance",
        "suspend guidance",
        "no longer providing guidance",
    ],
    "cybersecurity_incident_flag": [
        "material cybersecurity incident",
        "cybersecurity incident",
        "cyber incident",
        "security incident",
        "ransomware",
        "data breach",
    ],
}

FLAG_SECTION_SCOPE: dict[str, frozenset[str]] = {
    "material_weakness_flag": frozenset(
        {"item_9a_controls", "item_4_controls", "item_1a_risk_factors"}
    ),
    "significant_deficiency_flag": frozenset(
        {"item_9a_controls", "item_4_controls", "item_1a_risk_factors"}
    ),
    "ineffective_controls_flag": frozenset(
        {"item_9a_controls", "item_4_controls", "item_1a_risk_factors"}
    ),
    "restatement_flag": frozenset(
        {"item_9a_controls", "item_4_controls", "item_1a_risk_factors"}
    ),
    "non_reliance_flag": frozenset(
        {"item_9a_controls", "item_4_controls", "item_1a_risk_factors"}
    ),
    "auditor_change_flag": frozenset(
        {"item_9a_controls", "item_4_controls", "item_1a_risk_factors"}
    ),
    "investigation_flag": frozenset(
        {
            "item_1a_risk_factors",
            "item_3_legal_proceedings",
            "item_1_legal_proceedings",
            "item_1_01",
            "item_1_05",
            "item_8_01",
        }
    ),
    "settlement_flag": frozenset(
        {
            "item_1a_risk_factors",
            "item_3_legal_proceedings",
            "item_1_legal_proceedings",
            "item_1_01",
            "item_1_05",
            "item_8_01",
        }
    ),
    "material_legal_proceeding_flag": frozenset(
        {
            "item_1a_risk_factors",
            "item_3_legal_proceedings",
            "item_1_legal_proceedings",
            "item_1_01",
            "item_1_05",
            "item_8_01",
        }
    ),
    "going_concern_flag": frozenset(
        {"item_1a_risk_factors", "item_7_mdna", "item_2_mdna", "item_1_01", "item_8_01"}
    ),
    "covenant_breach_flag": frozenset(
        {"item_1a_risk_factors", "item_7_mdna", "item_2_mdna", "item_1_01", "item_8_01"}
    ),
    "guidance_withdrawal_flag": frozenset({"item_7_mdna", "item_2_mdna", "item_2_02"}),
    "cybersecurity_incident_flag": frozenset(
        {"item_1c_cybersecurity", "item_1_05", "item_8_01", "item_1a_risk_factors"}
    ),
}

MDNA_DENSITY_TERMS: dict[str, list[str]] = {
    "uncertainty_term_density": [
        "may",
        "might",
        "could",
        "uncertain",
        "uncertainty",
        "subject to",
        "volatile",
        "unpredictable",
    ],
    "demand_softness_density": [
        "soft demand",
        "demand declined",
        "lower demand",
        "weakened demand",
        "demand softness",
        "order slowdown",
    ],
    "margin_pressure_density": [
        "margin pressure",
        "compressed margins",
        "gross margin decline",
        "margin compression",
        "operating margin declined",
        "pricing pressure",
        "inflationary pressures",
        "lower gross margins",
        "margin headwinds",
    ],
    "liquidity_constraint_density": [
        "liquidity constraint",
        "cash constraint",
        "cash shortfall",
        "cash burn",
        "cash requirements",
        "debt maturity",
        "covenant pressure",
        "refinancing risk",
        "working capital",
    ],
}

MDNA_SECTIONS = frozenset({"item_7_mdna", "item_2_mdna"})
