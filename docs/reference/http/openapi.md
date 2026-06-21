# HTTP API (OpenAPI)

The REST API is a FastAPI application. Schema definitions are generated automatically at runtime.

## Interactive documentation

Start the server:

```bash
export SEC_USER_AGENT="YourName your@email.com"
disclosure-alpha-api
```

Then open:

| URL | Description |
|-----|-------------|
| `http://localhost:8000/docs` | Swagger UI (try requests) |
| `http://localhost:8000/redoc` | ReDoc |
| `http://localhost:8000/openapi.json` | OpenAPI 3 schema (for codegen) |

Default bind: `0.0.0.0:8000` — override with `HOST` and `PORT` env vars.

## Response models

Pydantic models in `disclosure_alpha.api.schemas`:

| Module | Primary models |
|--------|----------------|
| `schemas.matrix` | `MatrixResponse` |
| `schemas.flags` | Flags payload |
| `schemas.changes` | Changes payload |
| `schemas.panel` | Panel batch response |
| `schemas.common` | Shared filing metadata |

User-facing endpoint semantics: {doc}`../../guides/http/index`.

## HTTP status codes

| Code | When |
|------|------|
| **200** | Success |
| **404** | Filing not found for ticker / fiscal year / form |
| **402** | `view=composite` or `view=full` on matrix (not supported in OSS) |
| **422** | Invalid request (e.g. panel with more than 25 tickers) |
| **500** | Unexpected server error |

### 402 — composite not in open source

```bash
curl "http://localhost:8000/v1/company/AAPL/disclosure-matrix?view=composite"
# HTTP 402 — use view=deterministic
```

### 422 — panel limit

Panel POST accepts at most **25** tickers per request.

### SEC / EDGAR errors

Ticker routes require `SEC_USER_AGENT`. Missing or invalid User-Agent may cause upstream EDGAR failures surfaced as 404 or 500 depending on context. See {doc}`../../getting-started/faq`.

## Related

- {doc}`../../guides/http/index`
- {doc}`../environment-variables`
- {doc}`../section-taxonomy`
