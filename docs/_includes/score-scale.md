All component scores use **0–100**. Higher values mean more disclosure risk or deterioration, except for `specificity_quality_score` (higher = better specificity).

| Range | Interpretation |
|------:|----------------|
| 0–25 | Low concern |
| 26–50 | Moderate |
| 51–75 | Elevated |
| 76–100 | High |

**Specificity inversion:** Most components rise when language gets worse. `specificity_quality_score` is the opposite — a higher value means the filing is more specific (numbers, named entities, concrete detail). It is returned in `components` but is **not** part of the headline `overall_disclosure_risk_score` weights.
