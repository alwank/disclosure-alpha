# HTTP Endpoint Reference

Generated from the FastAPI OpenAPI schema (`disclosure_alpha.api.app_factory`).
Regenerate with:

```bash
python scripts/generate_http_endpoints_docs.py
```

Conceptual guide: {doc}`../../guides/http/index`. Interactive docs: {doc}`openapi`.

## Common errors

| Code | When |
|------|------|
| **404** | Filing not found for ticker / year / form |
| **422** | Invalid query or body (e.g. panel with >25 tickers) |
| **502** | Upstream EDGAR fetch failure |

## `GET /`

Openbb Root

**Response (200):** `object`

### Responses

| Status | Description |
|--------|-------------|
| **200** | Successful Response |

## `GET /agents.json`

Get Agents Json

**Response (200):** `object`

### Responses

| Status | Description |
|--------|-------------|
| **200** | Successful Response |

## `GET /apps.json`

Get Apps Json

**Response (200):** `object`

### Responses

| Status | Description |
|--------|-------------|
| **200** | Successful Response |

## `GET /health`

Health

**Response (200):** `object`

### Responses

| Status | Description |
|--------|-------------|
| **200** | Successful Response |

### Example

```bash
curl "http://localhost:8000/health"
```

## `GET /openbb/company`

Openbb Company

### Parameters

| Name | In | Required | Type | Description |
|------|-----|----------|------|-------------|
| `ticker` | query | no | string |  |
| `fiscal_year` | query | no | integer |  |
| `form_type` | query | no | string |  |
| `quarter` | query | no | object |  |
| `demo` | query | no | object |  |
| `scoring_model_version` | query | no | string |  |

### Responses

| Status | Description |
|--------|-------------|
| **200** | Successful Response |
| **422** | Validation Error |

### Example

```bash
curl -s "http://localhost:8000/openbb/company?demo=1" | head
```

## `GET /prompts.json`

Get Prompts Json

**Response (200):** `object`

### Responses

| Status | Description |
|--------|-------------|
| **200** | Successful Response |

## `GET /mcp`

Analyst MCP (Streamable HTTP)

Mounted when `disclosure-alpha[mcp]` is installed alongside `[api]`. Serves the **Disclosure Alpha Analyst** MCP server on the same process as `disclosure-alpha-api`. OpenBB Workspace connects from the app page via `mcp_servers` in `/apps.json`.

Not listed in the OpenAPI schema (ASGI sub-mount). Requires `pip install "disclosure-alpha[api,mcp]"`.

## `GET /templates.json`

Get Templates Json

**Response (200):** `object`

### Responses

| Status | Description |
|--------|-------------|
| **200** | Successful Response |

## `GET /v1/company/{ticker}/disclosure-changes`

Disclosure Changes

### Parameters

| Name | In | Required | Type | Description |
|------|-----|----------|------|-------------|
| `ticker` | path | yes | string |  |
| `fiscal_year` | query | yes | integer |  |
| `form_type` | query | no | string |  |
| `quarter` | query | no | object |  |
| `compare` | query | no | string |  |
| `sections` | query | no | object |  |
| `scoring_model_version` | query | no | string | Scoring model: deterministic_scoring_v2 (default) or deterministic_scoring_v1 |

**Response (200):** `ChangesResponse`

### Responses

| Status | Description |
|--------|-------------|
| **200** | Successful Response |
| **404** | Not Found |
| **422** | Unprocessable Entity |
| **502** | Bad Gateway |

### Example

```bash
curl "http://localhost:8000/v1/company/AAPL/disclosure-changes?fiscal_year=2025&form_type=10-K"
```

## `GET /v1/company/{ticker}/disclosure-flags`

Disclosure Flags

### Parameters

| Name | In | Required | Type | Description |
|------|-----|----------|------|-------------|
| `ticker` | path | yes | string |  |
| `fiscal_year` | query | yes | integer |  |
| `form_type` | query | no | string |  |
| `quarter` | query | no | object |  |
| `compare` | query | no | string |  |
| `sections` | query | no | object |  |

**Response (200):** `FlagsResponse`

### Responses

| Status | Description |
|--------|-------------|
| **200** | Successful Response |
| **404** | Not Found |
| **422** | Unprocessable Entity |
| **502** | Bad Gateway |

### Example

```bash
curl "http://localhost:8000/v1/company/AAPL/disclosure-flags?fiscal_year=2025&form_type=10-K"
```

## `GET /v1/company/{ticker}/disclosure-matrix`

Disclosure Matrix

### Parameters

| Name | In | Required | Type | Description |
|------|-----|----------|------|-------------|
| `ticker` | path | yes | string |  |
| `fiscal_year` | query | yes | integer |  |
| `form_type` | query | no | string |  |
| `quarter` | query | no | object |  |
| `compare` | query | no | string |  |
| `sections` | query | no | object |  |
| `include` | query | no | object |  |
| `fields` | query | no | object |  |
| `tier` | query | no | object | Response tier preset (lite\|standard\|analyst); overrides include/fields when set |
| `scoring_model_version` | query | no | string | Scoring model: deterministic_scoring_v2 (default) or deterministic_scoring_v1 |

**Response (200):** `MatrixResponse`

### Responses

| Status | Description |
|--------|-------------|
| **200** | Successful Response |
| **404** | Not Found |
| **422** | Unprocessable Entity |
| **502** | Bad Gateway |

### Example

```bash
curl "http://localhost:8000/v1/company/AAPL/disclosure-matrix?fiscal_year=2025&form_type=10-K"
```

## `GET /v1/company/{ticker}/disclosure-metrics`

Disclosure Metrics

### Parameters

| Name | In | Required | Type | Description |
|------|-----|----------|------|-------------|
| `ticker` | path | yes | string |  |
| `fiscal_year` | query | yes | integer |  |
| `form_type` | query | no | string |  |
| `quarter` | query | no | object |  |
| `compare` | query | no | string |  |
| `sections` | query | no | object |  |

**Response (200):** `MetricsResponse`

### Responses

| Status | Description |
|--------|-------------|
| **200** | Successful Response |
| **404** | Not Found |
| **422** | Unprocessable Entity |
| **502** | Bad Gateway |

### Example

```bash
curl "http://localhost:8000/v1/company/AAPL/disclosure-metrics?fiscal_year=2025&form_type=10-K"
```

## `GET /v1/company/{ticker}/filings`

Company Filings

### Parameters

| Name | In | Required | Type | Description |
|------|-----|----------|------|-------------|
| `ticker` | path | yes | string |  |
| `fiscal_year` | query | yes | integer |  |
| `form_type` | query | no | object |  |

**Response (200):** `FilingsResponse`

### Responses

| Status | Description |
|--------|-------------|
| **200** | Successful Response |
| **404** | Not Found |
| **422** | Validation Error |
| **502** | Bad Gateway |

### Example

```bash
curl "http://localhost:8000/v1/company/AAPL/filings?fiscal_year=2025&form_type=10-K"
```

## `GET /v1/company/{ticker}/sections`

Company Sections

### Parameters

| Name | In | Required | Type | Description |
|------|-----|----------|------|-------------|
| `ticker` | path | yes | string |  |
| `fiscal_year` | query | yes | integer |  |
| `form_type` | query | no | string |  |
| `quarter` | query | no | object |  |
| `compare` | query | no | string |  |
| `sections` | query | no | object |  |
| `include_text` | query | no | boolean |  |

**Response (200):** `SectionsResponse`

### Responses

| Status | Description |
|--------|-------------|
| **200** | Successful Response |
| **404** | Not Found |
| **422** | Unprocessable Entity |
| **502** | Bad Gateway |

### Example

```bash
curl "http://localhost:8000/v1/company/AAPL/sections?fiscal_year=2025&form_type=10-K"
```

## `POST /v1/panel/disclosure-matrix`

Panel Disclosure Matrix

**Request body:** `PanelRequest`


**Response (200):** `PanelResponse`

### Responses

| Status | Description |
|--------|-------------|
| **200** | Successful Response |
| **422** | Unprocessable Entity |

### Example

```bash
curl -s -X POST "http://localhost:8000/v1/panel/disclosure-matrix" \
  -H "Content-Type: application/json" \
  -d '{"tickers": ["AAPL", "MSFT"], "fiscal_year": 2025, "form_type": "10-K"}'
```

## `GET /widgets.json`

Get Widgets Json

**Response (200):** `object`

### Responses

| Status | Description |
|--------|-------------|
| **200** | Successful Response |

### Example

```bash
curl -s "http://localhost:8000/widgets.json" | jq 'keys'
```
