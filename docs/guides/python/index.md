# Python SDK Guide

Import `disclosure_alpha` to extract sections, compute metrics, and score filings in notebooks or applications — without the CLI or HTTP layer.

**Prerequisites:** {doc}`../../getting-started/installation`; {doc}`../../getting-started/sec-edgar-setup` for ticker helpers.

## High-level helpers

**Score local HTML:**

```python
from disclosure_alpha import score_filing_html

result = score_filing_html(open("filing.html").read(), "10-K")
print(result.scores.overall_disclosure_risk_score)
print(result.to_dict())
```

**Score by ticker:**

```python
from disclosure_alpha import score_filing_ticker

result = score_filing_ticker("AAPL", 2025, form_type="10-K")
print(result.scores.overall_disclosure_risk_score)
```

Optional prior filing for diffs:

```python
result = score_filing_html(html, "10-K", prior_html=prior_html)
```

## Pipeline stages

Use lower-level functions when you need control over each step:

```python
from disclosure_alpha import (
    extract_sections_from_html,
    compute_section_metrics,
    score_deterministic,
)

sections = extract_sections_from_html(html, form_type="10-K")
metrics = compute_section_metrics(sections, prior_sections=None)
scores = score_deterministic(metrics)
```

`extract_sections_from_html` returns a list of section objects with `section_name`, `cleaned_text`, `word_count`, and `extraction_confidence`.

## Result fields

`score_filing_*` returns a `ScoreResult` with:

- `scores.overall_disclosure_risk_score` — weighted headline (0–100)
- `scores.components` — ten computed scores (nine headline-weighted plus `specificity_quality_score`; some may be `None` if sections are missing)
- `scores.confidence_score` — derived from component coverage
- `scores.missing_components` — list of components that could not be computed

See {doc}`../../methodology/overview` for component definitions and {doc}`../../reference/section-taxonomy` for section names.

## Related

- {doc}`../../getting-started/quickstart-python`
- {doc}`../../getting-started/choose-your-surface`
- {doc}`../http/index`
