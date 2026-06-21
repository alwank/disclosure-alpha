# HTTP API package

**Typical use case:** Run `disclosure-alpha-api` behind your own service layer to expose filing scores, metrics, and batch panel screening to dashboards or internal tools — without embedding the Python SDK in every client.

The REST API is implemented with FastAPI. Route handlers live under `disclosure_alpha.api.endpoints`.

- **User guide:** {doc}`../../guides/http/index`
- **OpenAPI / schemas:** {doc}`../http/openapi`
- **Start server:** `disclosure-alpha-api` (requires `pip install "disclosure-alpha[api,dev]"`)

Interactive docs when the server is running:

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
