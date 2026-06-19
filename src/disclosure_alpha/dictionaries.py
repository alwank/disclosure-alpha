"""Built-in word lists for deterministic text metrics. Replaceable with licensed dictionaries."""

DICTIONARY_VERSION = "built_in_dictionaries_v2"

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
    "flags": {
        "source": "sec_pcaob_fasb_phrase_curated",
        "match_type": "phrase",
        "consumer": ["section_flags", "component_flag_boosts"],
        "license": "repo_safe_manual_curation",
    },
}

NEGATIVE_WORDS = frozenset(
    {
        "loss", "losses", "decline", "declined", "adverse", "adversely", "impairment",
        "deterioration", "weakness", "weak", "negative", "deficit", "shortfall",
        "downgrade", "failure", "failed", "harm", "damage", "breach", "default",
        "impaired", "impair", "impairments", "disruption", "disruptions", "disrupted",
        "bankruptcy", "bankrupt", "insolvency", "insolvent", "delinquency",
        "delinquencies", "delinquent", "writedown", "writeoff", "chargeoff",
        "chargeoffs", "recall", "recalls", "outage", "outages", "misstatement",
        "misstatements", "fraud", "fraudulent",
    }
)

UNCERTAINTY_WORDS = frozenset(
    {
        "may", "might", "could", "uncertain", "uncertainty", "volatility", "volatile",
        "unpredictable", "depend", "depends", "possible", "potentially",
        "approximate", "approximately", "contingency", "contingencies", "contingent",
        "fluctuate", "fluctuates", "fluctuation", "fluctuations", "variable",
        "variability", "unresolved", "pending", "exposure", "exposures", "exposed",
        "susceptible", "unforeseen", "undetermined", "assumption", "assumptions",
    }
)

LITIGIOUS_WORDS = frozenset(
    {
        "litigation", "lawsuit", "investigation", "inquiry", "regulatory", "enforcement",
        "claim", "claims", "proceeding", "proceedings", "subpoena", "subpoenas",
        "settlement", "complaint", "penalty", "penalties", "plaintiff", "defendant",
        "arbitration", "arbitrations", "appeal", "appeals", "appellate", "antitrust",
        "allegation", "allegations", "alleged", "damages", "injunction", "injunctive",
        "indemnification", "indemnify", "sanction", "sanctions", "decree",
    }
)

CONSTRAINING_WORDS = frozenset(
    {
        "covenant", "covenants", "restriction", "restrictions", "limitation", "limitations",
        "mandatory", "obligation", "obligations", "compliance", "constraint", "constraints",
        "default", "defaults", "breach", "breaches",
        "restricted", "restrictive", "waiver", "waivers", "forbearance", "acceleration",
        "accelerated", "maturity", "maturities", "refinance", "refinancing", "collateral",
        "lien", "liens", "pledged", "encumbered", "obligated",
    }
)

WEAK_MODAL_WORDS = frozenset({"may", "might", "could", "possibly", "possible"})
MODERATE_MODAL_WORDS = frozenset(
    {"should", "would", "expect", "expects", "believe", "believes", "intend", "intends"}
)
STRONG_MODAL_WORDS = frozenset({"must", "will", "shall", "required", "obligated"})
MODAL_WORDS = WEAK_MODAL_WORDS | MODERATE_MODAL_WORDS | STRONG_MODAL_WORDS

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
    "we face risks and uncertainties",
    "risks and uncertainties described below",
    "could materially and adversely affect",
    "material adverse effect on our business",
    "no assurance can be given",
    "may not be successful",
    "may fail to",
    "subject to a number of risks",
    "unknown risks and uncertainties",
    "not exhaustive",
]

GEOGRAPHY_TERMS = frozenset(
    {
        "americas", "europe", "asia", "china", "japan", "international", "domestic",
        "global", "region", "regions", "country", "countries", "north america",
        "latin america", "emea", "european union", "apac",
    }
)

SEGMENT_TERMS = frozenset(
    {
        "segment", "segments", "division", "divisions", "business unit", "product line",
        "brand", "brands", "channel", "channels", "market", "markets", "platform",
        "platforms", "subscription", "subscriptions", "service line", "service lines",
        "geography", "geographies",
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
        "civil investigative demand",
        "wells notice",
        "consent order",
        "consent decree",
        "cease and desist",
        "class action complaint",
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
        "working capital deficit",
        "negative working capital",
        "cash runway",
        "need to raise capital",
        "debt service",
        "near-term maturities",
        "credit facility availability",
        "borrowing base",
        "restricted cash",
    ],
    "supply chain": [
        "supplier",
        "supply chain",
        "supply chain disruption",
        "supply chain disruptions",
        "sourcing",
        "vendor",
        "single-source supplier",
        "sole supplier",
        "supplier concentration",
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
        "ransomware attack",
        "data exfiltration",
        "network intrusion",
        "unauthorized access",
    ],
    "customer concentration": [
        "major customer",
        "customer concentration",
        "largest customer",
        "significant customer",
        "top customer",
        "revenue concentration",
    ],
    "supplier concentration": [
        "sole supplier",
        "single supplier",
        "supplier concentration",
        "single-source supplier",
    ],
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
    "ai/data/privacy": [
        "artificial intelligence",
        "machine learning",
        "privacy law",
        "consumer data",
        "data processing",
        "model risk",
    ],
    "tax": ["tax audit", "tax examination", "uncertain tax position", "transfer pricing"],
    "credit/default": [
        "credit deterioration",
        "delinquency",
        "nonperforming",
        "charge-off",
        "chargeoff",
    ],
    "banking/capital": [
        "capital ratio",
        "risk-weighted assets",
        "liquidity coverage ratio",
        "stress capital buffer",
    ],
    "real estate": ["occupancy", "lease termination", "tenant default", "cap rate"],
    "healthcare/regulatory": [
        "fda approval",
        "clinical trial",
        "reimbursement",
        "cms",
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
    {
        "severe", "severely", "material", "materially", "significant", "significantly",
        "substantial", "substantially", "critical", "adverse", "major", "acute",
        "persistent", "prolonged", "widespread", "recurring",
    }
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
        "disclosure controls and procedures were ineffective",
        "internal control over financial reporting was not effective",
        "management concluded that our internal control over financial reporting was ineffective",
    ],
    "restatement_flag": [
        "restatement", "restated", "revision of previously issued",
        "will restate its financial statements",
    ],
    "non_reliance_flag": [
        "should no longer be relied upon", "non-reliance",
        "previously issued financial statements should no longer be relied upon",
        "audit committee concluded",
    ],
    "auditor_change_flag": ["change in certifying accountant", "resignation of our independent"],
    "investigation_flag": [
        "investigation",
        "subpoena",
        "received a subpoena",
        "subpoena from",
        "inquiry by the sec",
        "regulatory inquiry",
        "regulatory investigation",
        "civil investigative demand",
        "wells notice",
        "department of justice investigation",
    ],
    "settlement_flag": [
        "settlement", "consent decree", "civil penalty", "consent order",
        "cease and desist", "settled with the sec",
    ],
    "material_legal_proceeding_flag": [
        "material legal proceeding", "material litigation", "class action complaint",
        "enforcement action",
    ],
    "going_concern_flag": [
        "going concern",
        "continue as a going concern",
        "substantial doubt about our ability",
        "substantial doubt exists",
        "ability to continue as a going concern",
        "unable to meet obligations as they become due",
        "substantial doubt has not been alleviated",
    ],
    "covenant_breach_flag": [
        "covenant breach",
        "default under",
        "event of default",
        "default under our credit agreement",
        "violation of covenants",
        "breach of covenant",
        "failed to comply with covenants",
        "failed to comply with financial covenants",
        "breach of financial covenant",
        "waiver from lenders",
        "forbearance agreement",
        "accelerated repayment",
        "liquidity shortfall",
        "insufficient liquidity",
        "unable to refinance",
    ],
    "guidance_withdrawal_flag": [
        "withdraw our guidance",
        "withdraws guidance",
        "withdrawing guidance",
        "suspend guidance",
        "suspended guidance",
        "suspending guidance",
        "no longer providing guidance",
        "does not expect to provide guidance",
        "unable to provide guidance",
    ],
    "cybersecurity_incident_flag": [
        "material cybersecurity incident",
        "cybersecurity incident",
        "cyber incident",
        "security incident",
        "ransomware",
        "ransomware attack",
        "data breach",
        "unauthorized access",
        "data exfiltration",
        "data compromise",
        "network intrusion",
        "business email compromise",
        "personal information was accessed",
        "reasonably likely material impact",
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
        "subject to change",
        "volatile",
        "unpredictable",
        "known trends",
        "known uncertainties",
        "reasonably likely",
        "unable to predict",
        "cannot predict",
        "remains uncertain",
        "uncertain timing",
    ],
    "demand_softness_density": [
        "soft demand",
        "demand declined",
        "lower demand",
        "weakened demand",
        "demand softness",
        "order slowdown",
        "weaker demand",
        "reduced demand",
        "decline in demand",
        "order cancellations",
        "delayed orders",
        "customer destocking",
        "inventory correction",
        "lower volumes",
        "volume decline",
        "sales slowdown",
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
        "cost inflation",
        "input cost inflation",
        "higher input costs",
        "freight costs",
        "labor costs increased",
        "discounting",
        "promotional activity",
        "mix shift",
        "gross margin decreased",
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
        "working capital deficit",
        "negative working capital",
        "cash runway",
        "additional financing",
        "need to raise capital",
        "substantial doubt",
        "debt service",
        "near-term maturities",
        "credit facility availability",
        "borrowing base",
        "covenant compliance",
        "restricted cash",
    ],
}

MDNA_SECTIONS = frozenset({"item_7_mdna", "item_2_mdna"})
