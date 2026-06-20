# Product Surfaces

Disclosure Alpha exposes deterministic SEC filing analytics through **focused HTTP endpoints**, **MCP bundles**, and **response tiers** — without duplicating core pipeline logic in `pipeline.py`.

## Personas

| Persona | Need | Surface |
|---------|------|---------|
| Discovery / data engineer | List filings, extract sections | Filing Index + Section Extractor |
| Quant / researcher | Raw metrics, flags, diffs | Disclosure Analytics, Flags, Changes |
| Risk analyst | Filing-level scores | Disclosure Risk Score (matrix) |
| Screener / index builder | Batch tickers | Panel POST |
| Agent builder | Low-level pipeline in MCP | Builder MCP bundle |
| Agent user | Ticker score + filings | Analyst MCP bundle |

## HTTP API map

| Product | Method | Path | Tier |
|---------|--------|------|------|
| Health | `GET` | `/health` | infra |
| Filing Index | `GET` | `/v1/company/{ticker}/filings` | free |
| Section Extractor | `GET` | `/v1/company/{ticker}/sections` | free |
| Disclosure Analytics | `GET` | `/v1/company/{ticker}/disclosure-metrics` | free |
| Disclosure Risk Score | `GET` | `/v1/company/{ticker}/disclosure-matrix` | free (`deterministic`) / Pro stub (`composite`, `full`) |
| Risk Flags | `GET` | `/v1/company/{ticker}/disclosure-flags` | free |
| Filing Changes | `GET` | `/v1/company/{ticker}/disclosure-changes` | free |
| Panel Screener | `POST` | `/v1/panel/disclosure-matrix` | free (`deterministic`) |

All ticker endpoints share query params where applicable: `fiscal_year`, `form_type`, `quarter` (10-Q), `compare` (`prior`|`none`), `sections` (comma-separated filter).

## Matrix views and Pro boundary

| `view` | Status | Behavior |
|--------|--------|----------|
| `deterministic` | **Free** | Component scores from `deterministic_scoring_v3` |
| `composite` | **Pro stub** | HTTP **402** — LLM composite scoring not in open-source API |
| `full` | **Pro stub** | HTTP **402** — future bundle of deterministic + composite |

402 response shape:

```json
{
  "detail": "view=composite requires Disclosure Alpha Pro (composite LLM scoring not available in open-source API)",
  "available_views": ["deterministic"],
  "pro_required": true,
  "scoring_model_version": "deterministic_scoring_v3"
}
```

## Response tiers (matrix only)

Optional `tier` query param overrides `include` and `fields`:

| Tier | `include` | `fields` | Use case |
|------|-----------|----------|----------|
| `lite` | _(empty)_ | `overall` | Dashboard headline score |
| `standard` | `metrics` | `overall,components` | Research workflow |
| `analyst` | `metrics,provenance` | all | Audit / debugging |

Explicit `include` / `fields` still work when `tier` is omitted.

## MCP bundles

| Entry point | Tools | Resource |
|-------------|-------|----------|
| `disclosure-alpha-mcp-analyst` | `list_company_filings_tool`, `score_company_filing_tool` | `disclosure://taxonomy/v1` |
| `disclosure-alpha-mcp-builder` | `extract_sections_tool`, `compute_section_metrics_tool_wrapper`, `diff_sections_tool`, `score_deterministic_tool_wrapper`, `score_filing_html_tool_wrapper` | — |
| `disclosure-alpha-mcp` (legacy) | Alias → analyst | same taxonomy |

Legacy `disclosure-alpha-mcp` is deprecated for new integrations; use analyst or builder based on whether you need ticker helpers or raw HTML pipeline tools.

## Panel batch semantics

- Max **25** tickers per request (422 if exceeded).
- Per-ticker errors collected (`status: error`); request does not fail-fast.
- Only `view=deterministic` supported in v1.

## CLI (unchanged)

The CLI remains a single `disclosure-alpha` entry point (`extract`, `score`). Surface split applies to HTTP and MCP only; see [01_overview.md](./01_overview.md) for product tier table.

## Postman collections

Product-oriented collections under `docs/postman/`:

- `disclosure-alpha-discovery.postman_collection.json` — health + filings
- `disclosure-alpha-analytics.postman_collection.json` — sections + metrics
- `disclosure-alpha-scores.postman_collection.json` — matrix tiers + composite 402
- `disclosure-alpha-compliance.postman_collection.json` — flags + changes
- `disclosure-alpha-panel.postman_collection.json` — panel POST

Monolithic re-export: `disclosure-alpha-api.postman_collection.json` (full API).
