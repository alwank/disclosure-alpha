#!/usr/bin/env python3
"""Generate docs/reference/http/endpoints.md from the live FastAPI OpenAPI schema."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from disclosure_alpha.api.app_factory import create_app

OUT = Path(__file__).resolve().parents[1] / "docs" / "reference" / "http" / "endpoints.md"

_CURL_EXAMPLES: dict[tuple[str, str], str] = {
    ("get", "/health"): 'curl "http://localhost:8000/health"',
    ("get", "/v1/company/{ticker}/filings"): (
        'curl "http://localhost:8000/v1/company/AAPL/filings?fiscal_year=2025&form_type=10-K"'
    ),
    ("get", "/v1/company/{ticker}/sections"): (
        'curl "http://localhost:8000/v1/company/AAPL/sections?fiscal_year=2025&form_type=10-K"'
    ),
    ("get", "/v1/company/{ticker}/disclosure-metrics"): (
        'curl "http://localhost:8000/v1/company/AAPL/disclosure-metrics?fiscal_year=2025&form_type=10-K"'
    ),
    ("get", "/v1/company/{ticker}/disclosure-matrix"): (
        'curl "http://localhost:8000/v1/company/AAPL/disclosure-matrix?fiscal_year=2025&form_type=10-K"'
    ),
    ("get", "/v1/company/{ticker}/disclosure-flags"): (
        'curl "http://localhost:8000/v1/company/AAPL/disclosure-flags?fiscal_year=2025&form_type=10-K"'
    ),
    ("get", "/v1/company/{ticker}/disclosure-changes"): (
        'curl "http://localhost:8000/v1/company/AAPL/disclosure-changes?fiscal_year=2025&form_type=10-K"'
    ),
    ("post", "/v1/panel/disclosure-matrix"): (
        'curl -s -X POST "http://localhost:8000/v1/panel/disclosure-matrix" \\\n'
        '  -H "Content-Type: application/json" \\\n'
        '  -d \'{"tickers": ["AAPL", "MSFT"], "fiscal_year": 2025, "form_type": "10-K"}\''
    ),
    ("get", "/openbb/company"): 'curl -s "http://localhost:8000/openbb/company?demo=1" | head',
    ("get", "/widgets.json"): 'curl -s "http://localhost:8000/widgets.json" | jq \'keys\'',
}

# ponytail: ASGI-mounted routes not in OpenAPI — keep in sync with docs/guides/openbb
_MANUAL_BEFORE_TEMPLATES = """\
## `GET /mcp`

Analyst MCP (Streamable HTTP)

Mounted when `disclosure-alpha[mcp]` is installed alongside `[api]`. Serves the **Disclosure Alpha Analyst** MCP server on the same process as `disclosure-alpha-api`. OpenBB Workspace connects from the app page via `mcp_servers` in `/apps.json`.

Not listed in the OpenAPI schema (ASGI sub-mount). Requires `pip install "disclosure-alpha[api,mcp]"`.

"""


def _ref_name(schema: dict) -> str:
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    if schema.get("type") == "array" and "items" in schema:
        return f"array[{_ref_name(schema['items'])}]"
    return schema.get("type", "object")


def _params_table(parameters: list[dict]) -> str:
    if not parameters:
        return ""
    lines = ["| Name | In | Required | Type | Description |", "|------|-----|----------|------|-------------|"]
    for p in parameters:
        schema = p.get("schema", {})
        ptype = schema.get("type") or _ref_name(schema)
        desc = (p.get("description") or "").replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| `{p['name']}` | {p.get('in', '')} | {'yes' if p.get('required') else 'no'} "
            f"| {ptype} | {desc} |"
        )
    return "\n".join(lines) + "\n"


def _responses_table(responses: dict) -> str:
    lines = ["| Status | Description |", "|--------|-------------|"]
    for code, info in sorted(responses.items(), key=lambda x: x[0]):
        desc = (info.get("description") or "").replace("|", "\\|")
        lines.append(f"| **{code}** | {desc} |")
    return "\n".join(lines)


def _body_section(request_body: dict | None) -> str:
    if not request_body:
        return ""
    content = request_body.get("content", {}).get("application/json", {})
    schema = content.get("schema", {})
    model = _ref_name(schema)
    return f"**Request body:** `{model}`\n\n"


def generate() -> str:
    spec = create_app().openapi()
    lines = [
        "# HTTP Endpoint Reference",
        "",
        "Generated from the FastAPI OpenAPI schema (`disclosure_alpha.api.app_factory`).",
        "Regenerate with:",
        "",
        "```bash",
        "python scripts/generate_http_endpoints_docs.py",
        "```",
        "",
        "Conceptual guide: {doc}`../../guides/http/index`. Interactive docs: {doc}`openapi`.",
        "",
        "## Common errors",
        "",
        "| Code | When |",
        "|------|------|",
        "| **404** | Filing not found for ticker / year / form |",
        "| **422** | Invalid query or body (e.g. panel with >25 tickers) |",
        "| **502** | Upstream EDGAR fetch failure |",
        "",
    ]

    paths = spec.get("paths", {})
    for path in sorted(paths):
        for method, op in sorted(paths[path].items()):
            if method not in {"get", "post", "put", "delete", "patch"}:
                continue
            summary = op.get("summary") or op.get("operationId", path)
            lines.extend([f"## `{method.upper()} {path}`", "", summary, ""])
            params = _params_table(op.get("parameters", []))
            if params:
                lines.extend(["### Parameters", "", params])
            body = _body_section(op.get("requestBody"))
            if body:
                lines.extend([body])
            success = op.get("responses", {}).get("200", {})
            if success:
                content = success.get("content", {}).get("application/json", {})
                if content:
                    model = _ref_name(content.get("schema", {}))
                    lines.append(f"**Response (200):** `{model}`\n")
            lines.extend(["### Responses", "", _responses_table(op.get("responses", {})), ""])
            curl = _CURL_EXAMPLES.get((method, path))
            if curl:
                lines.extend(["### Example", "", "```bash", curl, "```", ""])

    body = "\n".join(lines).rstrip() + "\n"
    marker = "## `GET /templates.json`"
    if marker in body:
        body = body.replace(marker, _MANUAL_BEFORE_TEMPLATES + marker, 1)
    return body


def check() -> None:
    before = OUT.read_text(encoding="utf-8") if OUT.is_file() else ""
    generated = generate()
    if before != generated:
        raise SystemExit("docs/reference/http/endpoints.md drift (run without --check to refresh)")
    print("docs/reference/http/endpoints.md OK")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Regenerate in memory and fail if committed file differs",
    )
    args = parser.parse_args()
    if args.check:
        check()
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(generate(), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
