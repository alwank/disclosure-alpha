# Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SEC_USER_AGENT` | Yes (EDGAR) | — | Descriptive User-Agent for SEC requests, e.g. `YourName your@email.com` |
| `DISCLOSURE_ALPHA_CACHE_DIR` | No | `data/cache/sec_filings` | Directory for cached EDGAR filings |
| `HOST` | No | `0.0.0.0` | HTTP API bind address |
| `PORT` | No | `8000` | HTTP API port |
| `EMBEDDING_BACKEND` | No | _(model default)_ | Set to `tfidf` to force TF-IDF embeddings |
| `OPENBB_API_URL` | No | OpenBB default | Base URL for optional post-filing outcome fetch (`[outcomes]` extra) |
| `SPACY_MODEL` | No | `en_core_web_sm` | spaCy model for construct-validity harness (optional `[validation]` extra) |
| `DISCLOSURE_ALPHA_VALIDATION_CACHE_DIR` | No | `data/validation/cache` | Cache directory for internal validation artifacts |
| `SEC_USER_AGENT_WORKER_0...N` | No | — | Optional per-worker SEC identities when running multi-process EDGAR builds |

Set `SEC_USER_AGENT` in the shell or process environment before running ticker-based CLI, HTTP, or MCP commands. See {doc}`../getting-started/sec-edgar-setup`.
