# pipeline

**Use when:** You want the full in-memory path from filing HTML (or EDGAR ticker) to deterministic scores in one call — or you need step-by-step control over extraction, metrics, and aggregation.

## Start here

- **`score_filing_html()`** — score local HTML; optional `prior_html` for diffs
- **`score_filing_ticker()`** — fetch from EDGAR by ticker, fiscal year, and form type
- **`compute_section_metrics()`** — extract metrics, flags, diffs without aggregating to components
- **`extract_sections_from_html()`** — section extraction only
- **`score_deterministic()`** — aggregate an existing `MetricsResult`
- **`FilingScoreResult`** — typed result with `.scores` and `.to_dict()`

## Example

```python
from disclosure_alpha import score_filing_html, score_filing_ticker

# Local HTML
result = score_filing_html(open("filing.html").read(), "10-K")
print(result.scores.overall_disclosure_risk_score)

# EDGAR (requires SEC_USER_AGENT)
result = score_filing_ticker("AAPL", 2025, form_type="10-K")
print(result.to_dict()["scores"]["components"])
```

## Full API

```{eval-rst}
.. automodule:: disclosure_alpha.pipeline
   :members: score_filing_html, score_filing_ticker, compute_section_metrics, extract_sections_from_html, score_deterministic, FilingScoreResult, MetricsResult
```
