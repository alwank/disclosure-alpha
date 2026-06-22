# HTTP API (OpenAPI)

The REST API is a FastAPI application. Schema definitions are generated automatically at runtime.

## Export OpenAPI JSON

With the server running:

```bash
curl -s http://localhost:8000/openapi.json -o openapi.json
```

Or without starting the server (from a dev checkout):

```bash
python scripts/generate_http_endpoints_docs.py   # also refreshes endpoint reference
python -c "from disclosure_alpha.api.app_factory import create_app; import json; print(json.dumps(create_app().openapi(), indent=2))" > openapi.json
```

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

## Endpoint reference

Per-route parameters, responses, and curl examples: {doc}`endpoints` (generated from the live FastAPI schema).

User-facing endpoint semantics: {doc}`../../guides/http/index`.

## HTTP status codes

| Code | When |
|------|------|
| **200** | Success |
| **404** | Filing not found for ticker / fiscal year / form |
| **422** | Invalid request (e.g. panel with more than 25 tickers) |
| **500** | Unexpected server error |

### SEC / EDGAR errors

Ticker routes require `SEC_USER_AGENT`. Missing or invalid User-Agent may cause upstream EDGAR failures surfaced as 404 or 500 depending on context. See {doc}`../../getting-started/faq`.

## Related

- {doc}`endpoints`
- {doc}`../../guides/http/index`
- {doc}`../../guides/production`
- {doc}`../environment-variables`
- {doc}`../section-taxonomy`
