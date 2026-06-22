# Quickstart: Python API

Score a filing from Python in a few lines.

**Audience:** Notebook and application developers.
**Before you start:** {doc}`installation`; {doc}`sec-edgar-setup` for ticker helpers.

## Summary

Import `score_filing_html` or `score_filing_ticker` and read `.scores` from the result object.

## Score local HTML

**Goal:** Score HTML you already have — no EDGAR fetch.

```python
from disclosure_alpha import score_filing_html

with open("filing.html", encoding="utf-8") as f:
    result = score_filing_html(f.read(), "10-K")
print(result.scores.overall_disclosure_risk_score)
print(list(result.to_dict().keys()))
```

`score_filing_html` returns a structured result object; `result.to_dict()` is the full JSON-serializable dict (sections, metrics, scores, versions).

### Sample output

Key fields from the committed minimal 10-K fixture:

```{literalinclude} ../examples/score-minimal-10k.json
:language: json
:lines: 124-145
```

### How to read it

- **`result.scores.overall_disclosure_risk_score`** — same headline field as CLI JSON
- **`result.to_dict()`** — full structure including sections, metrics, and versions
- Pass `prior_html=` to populate change-related components

### If something looks wrong

Null `disclosure_change_score` without prior HTML is expected: {doc}`faq`.

## Score by ticker

**Goal:** Let the SDK fetch and score from EDGAR.

```python
import os
os.environ["SEC_USER_AGENT"] = "YourName your@email.com"

from disclosure_alpha import score_filing_ticker

result = score_filing_ticker("AAPL", 2025, form_type="10-K")
print(result.scores.overall_disclosure_risk_score)
```

### How to read it

- Prior filing is resolved automatically for diffs when available
- Check `result.scores.score_coverage_ratio` before comparing across tickers
- Use `result.to_dict()["scores"]["components"]` for component-level analysis

### If something looks wrong

See {doc}`faq` for EDGAR and coverage issues.

## Lower-level pipeline

**Goal:** Control extraction, metrics, and aggregation separately.

```python
from disclosure_alpha import extract_sections_from_html, compute_section_metrics, score_deterministic

sections = extract_sections_from_html(html, form_type="10-K")
metrics = compute_section_metrics(sections)
scores = score_deterministic(metrics)
```

Use this when you need intermediate metrics without filing-level aggregation shortcuts.

## Related

- {doc}`understanding-scores` — interpret score JSON
- {doc}`../guides/python/index` — SDK walkthrough
- {doc}`choose-your-surface`
