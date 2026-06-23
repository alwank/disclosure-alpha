"""Section-scoped event flag patterns and suppressions."""

FLAG_PATTERNS: dict[str, list[str]] = {
    "material_weakness_flag": [
        "material weakness",
        "material weaknesses",
        "material weakness in internal control over financial reporting",
        "material weaknesses in internal control over financial reporting",
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
        "plans are intended to mitigate",
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
        "no longer expects",
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
        "incident response",
        "systems outage",
    ],
}

FLAG_SUPPRESSIONS: dict[str, list[str]] = {
    "material_weakness_flag": [
        "no material weakness",
        "no material weaknesses",
        "did not identify any material weakness",
        "did not identify a material weakness",
        "no material weaknesses were identified",
    ],
    "going_concern_flag": [
        "substantial doubt has been alleviated",
        "alleviated substantial doubt",
    ],
    "cybersecurity_incident_flag": [
        "board oversight",
        "annual training",
        "cybersecurity program includes",
    ],
    "investigation_flag": [
        "routine regulatory examination",
        "periodic examination",
        "routine regulatory examinations",
    ],
    "covenant_breach_flag": [
        "default settings",
        "default rate",
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
