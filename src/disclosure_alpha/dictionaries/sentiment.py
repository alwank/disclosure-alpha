"""Token lists for tone and modal metrics."""

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
