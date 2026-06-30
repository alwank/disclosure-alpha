# Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SEC_USER_AGENT` | Yes (EDGAR) | — | Descriptive User-Agent for SEC requests, e.g. `YourName your@email.com` |
| `DISCLOSURE_ALPHA_CACHE_DIR` | No | `data/cache/sec_filings` | Directory for cached EDGAR filings |
| `HOST` | No | `0.0.0.0` | HTTP API bind address |
| `PORT` | No | `8000` | HTTP API port |
| `OPENBB_CORS_ORIGINS` | No | `https://pro.openbb.co,https://pro.openbb.dev,http://localhost:3000` | CORS origins for OpenBB Workspace browser access |
| `EMBEDDING_BACKEND` | No | `tfidf` when using `disclosure-alpha-api`; _(model default)_ elsewhere | `tfidf` avoids loading sentence-transformers; set `semantic` for MiniLM embeddings |
| `METRICS_CACHE_TTL_SECONDS` | No | `300` | In-process TTL for `metrics_filing_ticker` results (`0` disables) |
| `METRICS_CACHE_MAX_SIZE` | No | `64` | Max cached filing-metric entries per API worker (FIFO eviction) |
| `PANEL_MAX_WORKERS` | No | `4` | Concurrent tickers for panel screener (`score_panel_tickers`) |
| `PIPELINE_TIMING` | No | `1` when using `disclosure-alpha-api`; off elsewhere | Log per-stage seconds (`edgar`, `parse`, `parse_prior`, `metrics`, `diff`) on each `metrics_filing_ticker` run |
| `OPENBB_API_URL` | No | OpenBB default | Base URL for optional post-filing outcome fetch (`[outcomes]` extra only — **not** the Workspace connect URL; set backend URL in the Workspace UI) |
| `SPACY_MODEL` | No | `en_core_web_sm` | spaCy model for construct-validity harness (optional `[validation]` extra) |
| `DISCLOSURE_ALPHA_VALIDATION_CACHE_DIR` | No | `data/validation/cache` | Cache directory for optional validation harness runs |
| `SEC_USER_AGENT_WORKER_0...N` | No | — | Optional per-worker SEC identities when running multi-process EDGAR builds |

Set `SEC_USER_AGENT` in the shell or process environment before running ticker-based CLI, HTTP, or MCP commands. See {doc}`../getting-started/sec-edgar-setup`.
