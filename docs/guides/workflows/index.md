# Workflows

End-to-end recipes for common Disclosure Alpha tasks.

**Audience:** Users who know their goal and want a copy-paste path.
**Before you start:** {doc}`../../getting-started/installation` and {doc}`../../getting-started/sec-edgar-setup` for EDGAR-backed examples.

## Score one ticker and read the JSON (CLI)

**Goal:** Get a headline score and component breakdown for one company.

```bash
export SEC_USER_AGENT="YourName your@email.com"
disclosure-alpha score --ticker AAPL --fiscal-year 2025 --form 10-K \
  | jq '{overall: .scores.overall_disclosure_risk_score, coverage: .scores.score_coverage_ratio, components: .scores.components}'
```

### Sample output

```{literalinclude} ../../examples/score-minimal-10k.json
:language: json
:lines: 124-145
```

(Shape matches live CLI output; values differ by filing.)

### How to read it

- **`overall_disclosure_risk_score`** — headline 0–100; see {doc}`../../getting-started/understanding-scores`
- **`score_coverage_ratio`** — how many headline components were computed
- **`missing_components`** — often missing MD&A or no prior filing for change score

### If something looks wrong

{doc}`../../getting-started/faq` and {doc}`../cli/index`.

## Batch panel screen (HTTP)

**Goal:** Score up to 25 tickers in one request for a screener or dashboard.

Start the API:

```bash
export SEC_USER_AGENT="YourName your@email.com"
disclosure-alpha-api
```

Screen tickers:

```bash
curl -s -X POST "http://localhost:8000/v1/panel/disclosure-matrix" \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": ["AAPL", "MSFT", "GOOGL"],
    "fiscal_year": 2025,
    "form_type": "10-K"
  }' | jq '.results[] | {ticker, status, overall: .scores.overall_disclosure_risk_score}'
```

### Sample output

```{literalinclude} ../../examples/panel-response-snippet.json
:language: json
```

### How to read it

- **`results[].status`** — `"ok"` or `"error"` per ticker; the request does not fail-fast
- **`results[].scores`** — same score shape as CLI when status is ok
- **`summary`** — count of successes vs failures

### If something looks wrong

Panel 422 (>25 tickers) and per-ticker errors: {doc}`../../getting-started/faq`.

## Notebook: score and inspect components (Python)

**Goal:** Explore component scores interactively in a notebook.

```python
import os
os.environ["SEC_USER_AGENT"] = "YourName your@email.com"

from disclosure_alpha import score_filing_ticker

result = score_filing_ticker("AAPL", 2025, form_type="10-K")
scores = result.scores
print(scores.overall_disclosure_risk_score, scores.score_coverage_ratio)
for name, value in scores.components.__dict__.items():
    if value is not None:
        print(f"{name}: {value:.1f}")
```

### Sample output

Use the scores block from {doc}`../../getting-started/understanding-scores` as a reference for field names.

### How to read it

- Sort components by value to see which language signals dominate
- Compare `specificity_quality_score` separately — higher is better (inverse of most components)
- Request provenance from `result.to_dict()["scores"]["provenance"]` for audit trails

### If something looks wrong

{doc}`../../getting-started/faq`.

## Agent workflow: MCP analyst vs builder

**Goal:** Wire Disclosure Alpha into an MCP client.

**Analyst** — your agent knows tickers, not raw HTML:

```bash
disclosure-alpha-mcp-analyst
```

Tools: `list_company_filings_tool`, `score_company_filing_tool`.

**Builder** — your agent has filing HTML and needs pipeline steps:

```bash
disclosure-alpha-mcp-builder
```

Tools: `extract_sections_tool`, `compute_section_metrics_tool_wrapper`, `score_filing_html_tool_wrapper`, etc.

Configure `SEC_USER_AGENT` in env. See {doc}`../mcp/index`.

## Local HTML only (no EDGAR)

**Goal:** Score offline with current and prior HTML files.

```bash
disclosure-alpha score --html filing.html --form 10-K \
  --prior-html prior.html \
  | jq '.scores.overall_disclosure_risk_score'
```

With prior HTML, `disclosure_change_score` populates when matching sections exist:

```{literalinclude} ../../examples/score-with-prior-snippet.json
:language: json
:lines: 1-12
```

No network or `SEC_USER_AGENT` required when both files are local.

## Score in OpenBB Workspace (demo then live)

**Goal:** Run the Disclosure Company widget in OpenBB Workspace — sample data first, then live EDGAR.

See {doc}`../../getting-started/quickstart-openbb` for install, demo, and connect steps. Summary:

1. Start `disclosure-alpha-api` with `SEC_USER_AGENT` set for live scoring.
2. Connect Workspace (**Chrome**, URL `http://127.0.0.1:8000`).
3. **My Apps → Disclosure Alpha → Company** — Run with **`demo=1`**, then clear **`demo`** and Run again for live EDGAR.

### How to read it

Same score card as the HTTP matrix headline view: overall score, components, active flags, and section changes. See {doc}`../../getting-started/understanding-scores`.

### If something looks wrong

Chrome Local Network Access, Test 500, and Safari blocks: {doc}`../openbb/index` and {doc}`../../getting-started/quickstart-openbb`.

## Related

- {doc}`../../examples/index`
- {doc}`../../getting-started/choose-your-surface`
- {doc}`../../getting-started/understanding-scores`
- {doc}`../python/index`
- {doc}`../http/index`
- {doc}`../openbb/index`
