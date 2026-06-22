# Architecture

**Audience:** Contributors extending the pipeline or adding surfaces.

## Summary

High-level layout of Disclosure Alpha: EDGAR ingestion, section extraction, text metrics, deterministic scoring, and delivery surfaces (CLI, HTTP API, MCP).

## In plain terms

Filings are parsed into Item 1A text, scored with deterministic dictionaries and metrics, and exposed through library, CLI, HTTP, and MCP entry points. See repository `CONTRIBUTING.md` for install and validation workflows.

## Main content

Detailed architecture documentation is not yet published here. For now:

- Package layout: `src/disclosure_alpha/`
- **HTTP app factory:** import `create_app` from `disclosure_alpha.api.app_factory` (canonical). `disclosure_alpha.api.routes:app` is a backward-compat shim for uvicorn/ASGI hosts.
- Methodology overview: {doc}`../methodology/overview`
- Validation evidence: {doc}`../validation/evidence-and-limitations`

## Related

- {doc}`testing` — test commands and CI expectations
- Repository [CONTRIBUTING.md](https://github.com/alwank/disclosure-alpha/blob/main/CONTRIBUTING.md)
