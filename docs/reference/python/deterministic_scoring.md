# deterministic_scoring

**Use when:** You already have section metrics, diffs, flags, and densities as dicts and want filing-level component scores without running the full pipeline — for custom pipelines or tests.

## Start here

- **`aggregate_deterministic_matrix()`** — blend inputs into component scores, coverage, and confidence
- **`DeterministicAggregationResult`** — output dataclass with `.components`, `.overall_disclosure_risk_score`, etc.

For most applications, prefer `score_filing_html()` or `score_deterministic()` in {doc}`pipeline` — they assemble inputs automatically.

## Example

```python
from disclosure_alpha import aggregate_deterministic_matrix

result = aggregate_deterministic_matrix(
    section_metrics={"item_1a_risk_factors": {"negative_word_ratio": 0.02, ...}},
    section_diffs={"item_1a_risk_factors": 35.0},
    section_flags={"item_1a_risk_factors": {"investigation_flag": False}},
)
print(result.overall_disclosure_risk_score)
```

## Full API

```{eval-rst}
.. automodule:: disclosure_alpha.deterministic_scoring
   :members: aggregate_deterministic_matrix, DeterministicAggregationResult, DeterministicComponentProvenance
```
