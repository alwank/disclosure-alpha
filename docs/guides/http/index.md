# HTTP API Guide

REST endpoints for filings, sections, metrics, scores, flags, changes, and batch panel screening.

**Audience:** Backend developers integrating the REST API.
**Before you start:** `pip install "disclosure-alpha[api]"` (see {doc}`../../getting-started/installation`) and {doc}`../../getting-started/sec-edgar-setup`.

## Typical journeys

- **Dashboard headline** — `GET /v1/company/{ticker}/disclosure-matrix?tier=lite` for `overall_disclosure_risk_score` only
- **Research workflow** — `tier=standard` for overall + component scores with metrics attached
- **Audit / debugging** — `tier=analyst` with `include=metrics,provenance` for full score breakdown and input provenance

Interpret matrix JSON using {doc}`../../getting-started/understanding-scores`.

```{admonition} Security
:class: warning

The local API server has **no built-in authentication**. Do not expose it publicly without your own gateway. See {doc}`../production`.
```

## Annotated matrix response

Scores block from the committed minimal 10-K fixture (same shape as `/disclosure-matrix`):

```{literalinclude} ../../examples/score-minimal-10k.json
:language: json
:lines: 124-145
```

- **`overall_disclosure_risk_score`** — headline 0–100 for sorting and dashboards
- **`score_coverage_ratio`** / **`missing_components`** — data quality before comparing tickers
- **`components`** — ten computed scores (nine headline-weighted plus `specificity_quality_score`); null means not computed (not zero)

With `tier=lite`, only the headline field is returned. With `tier=analyst`, add metrics and provenance arrays.

## Endpoint map

| Product | Method | Path | Use when… |
|---------|--------|------|-----------|
| Health | `GET` | `/health` | …checking the server is up before batch jobs |
| Filing Index | `GET` | `/v1/company/{ticker}/filings` | …listing available filings for a ticker |
| Section Extractor | `GET` | `/v1/company/{ticker}/sections` | …debugging extraction or fetching section text |
| Disclosure Analytics | `GET` | `/v1/company/{ticker}/disclosure-metrics` | …you need raw metrics, flags, and diffs without aggregation |
| Disclosure Risk Score | `GET` | `/v1/company/{ticker}/disclosure-matrix` | …you need filing-level component scores for one ticker |
| Risk Flags | `GET` | `/v1/company/{ticker}/disclosure-flags` | …boolean risk events only |
| Filing Changes | `GET` | `/v1/company/{ticker}/disclosure-changes` | …year-over-year diff details without full scores |
| Panel Screener | `POST` | `/v1/panel/disclosure-matrix` | …batch-screening up to 25 tickers |

Shared query params on ticker routes: `fiscal_year`, `form_type`, `quarter` (10-Q), `compare` (`prior`|`none`), `sections` (comma-separated filter).

## Start the server

```bash
export SEC_USER_AGENT="YourName your@email.com"
disclosure-alpha-api
# listens on 0.0.0.0:8000 (override with HOST / PORT env)
```

## Response tiers (matrix only)

Optional `tier` query param overrides `include` and `fields`:

| Tier | `include` | `fields` | Use case |
|------|-----------|----------|----------|
| `lite` | _(empty)_ | `overall` | Dashboard headline score |
| `standard` | `metrics` | `overall,components` | Research workflow |
| `analyst` | `metrics,provenance` | all | Audit / debugging |

**Shared query params** (`sections`, `disclosure-metrics`, `disclosure-matrix`):

| Param | Default | Description |
|-------|---------|-------------|
| `compare` | `prior` | `prior` loads prior filing for diffs; `none` skips comparison |
| `sections` | all | Comma-separated section names; on **disclosure-matrix**, filters both returned metrics and computed scores (not filing-level scores from unfiltered sections). Panel has no section filter. |

**Matrix-only params:**

| Param | Default | Description |
|-------|---------|-------------|
| `tier` | — | `lite`, `standard`, or `analyst` |
| `include` | `metrics,provenance` | Comma-set: `metrics`, `provenance`. Empty → scores only |
| `fields` | all | Slim scores, e.g. `fields=overall,components` |
| `scoring_model_version` | `deterministic_scoring_v2` | Legacy `deterministic_scoring_v1` via matrix GET and panel POST |

## Example requests

```bash
curl "http://localhost:8000/v1/company/AAPL/disclosure-matrix?fiscal_year=2025&form_type=10-K"
curl "http://localhost:8000/v1/company/AAPL/disclosure-matrix?fiscal_year=2025&include="
curl "http://localhost:8000/v1/company/AAPL/disclosure-metrics?fiscal_year=2025&form_type=10-K&compare=none"
curl "http://localhost:8000/v1/company/AAPL/sections?fiscal_year=2025&sections=item_1a_risk_factors"
```

## Panel batch semantics

- Max **25** tickers per request (422 if exceeded).
- Per-ticker errors collected (`status: error`); request does not fail-fast.
- Optional `scoring_model_version` in request body (default `deterministic_scoring_v2`; legacy `deterministic_scoring_v1`).

Sample panel response: {doc}`../../examples/index`.

## Postman collections

Import-ready collections and response examples: {doc}`../../examples/index`.

## OpenAPI

With `disclosure-alpha-api` running:

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

Endpoint reference (generated from schema): {doc}`../../reference/http/endpoints`. Status codes: {doc}`../../reference/http/openapi`.

## HTTP errors

| Code | Cause |
|------|--------|
| **404** | Filing not found for ticker / year / form |
| **422** | Invalid body (e.g. panel with >25 tickers) |

See {doc}`../../getting-started/faq`.

## Related

- {doc}`../../getting-started/understanding-scores`
- {doc}`../../getting-started/choose-your-surface`
- {doc}`../../reference/http/endpoints`
- {doc}`../../reference/http/openapi`
- {doc}`../production`
- {doc}`../../examples/index`
- {doc}`../../reference/section-taxonomy`
- {doc}`../../reference/environment-variables`
- {doc}`../../methodology/overview`
