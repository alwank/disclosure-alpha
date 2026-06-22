# Python API Reference

Public Python modules. High-level helpers are also exported from `disclosure_alpha`.

## Most users start with these helpers

| Function | Use when |
|----------|----------|
| `score_filing_html(html, form_type)` | You have filing HTML on disk or in memory |
| `score_filing_ticker(ticker, fiscal_year, ...)` | Let the SDK fetch from EDGAR |
| `extract_sections_from_html(html, form_type)` | You need section text before custom metrics |

Quickstart: {doc}`../../getting-started/quickstart-python`. Version fields in output: {doc}`../versioning`.

```{toctree}
:maxdepth: 1

pipeline
cli
section_extractor
text_metrics
diff_engine
deterministic_scoring
dictionaries
edgar
mcp
api
```
