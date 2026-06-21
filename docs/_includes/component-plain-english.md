Nine deterministic components feed the headline `overall_disclosure_risk_score` (weights in `methodology/aggregation`). `specificity_quality_score` is also returned but excluded from headline weights — see the score scale include for its inversion.

| Plain English | JSON field | Primary section(s) |
|---------------|------------|--------------------|
| Risk-factor tone & volatility | `risk_factor_intensity_score` | Item 1A |
| Year-over-year disclosure change | `disclosure_change_score` | Item 1A, MD&A |
| MD&A uncertainty & demand stress | `mdna_uncertainty_score` | Item 7 (10-K) / Item 2 (10-Q) |
| Legal & regulatory risk language | `legal_regulatory_risk_score` | Item 1A (+ flags) |
| Liquidity & covenant stress | `liquidity_stress_score` | MD&A (+ flags) |
| Boilerplate & vague risk language | `boilerplate_risk_score` | Item 1A |
| Internal controls weakness signals | `internal_controls_risk_score` | Controls disclosure + Item 1A |
| Material event severity (diff-only) | `event_severity_score` | Item 1A |
| Cross-section negative tone | `tone_negativity_score` | Item 1A + MD&A |
