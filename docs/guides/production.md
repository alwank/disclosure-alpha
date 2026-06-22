# Production Notes

Running `disclosure-alpha-api` beyond local development.

## Deployment model

The open-source server is a **single-process FastAPI app** with no built-in authentication, rate limiting, or multi-tenant isolation. Put it behind your own API gateway, reverse proxy, or private network before exposing it publicly.

```bash
export SEC_USER_AGENT="YourOrg ops@example.com"
export DISCLOSURE_ALPHA_CACHE_DIR="/var/cache/disclosure-alpha"
disclosure-alpha-api
# default: 0.0.0.0:8000 — override HOST / PORT
```

## Required environment variables

| Variable | Required | Notes |
|----------|----------|-------|
| `SEC_USER_AGENT` | Yes (ticker routes) | Real org name + contact email — see {doc}`../getting-started/sec-edgar-setup` |
| `HOST` / `PORT` | No | Bind address (default `0.0.0.0:8000`) |
| `DISCLOSURE_ALPHA_CACHE_DIR` | No | EDGAR filing cache (speeds repeat requests) |

Full list: {doc}`../reference/environment-variables`.

## SEC fair access

- One descriptive User-Agent per deployment (or per worker pool)
- Respect SEC rate limits; the client includes polite delays
- Do not redistribute bulk-downloaded filings without reviewing [SEC terms](https://www.sec.gov/os/webmaster-faq#code-support)

Legal summary: {doc}`../legal`.

## SEC rate limits and workers

The EDGAR client enforces a per-process throttle (~9 requests/second) using a global lock on `_last_request_at`. That protects a single worker from hammering SEC, but it does **not** coordinate across processes.

| Deployment | Guidance |
|------------|----------|
| Single worker | One `SEC_USER_AGENT`; built-in throttle is sufficient |
| Multiple workers | **One SEC identity per worker** (separate `SEC_USER_AGENT` values), **or** enforce a shared rate limit at your reverse proxy / API gateway |
| Shared identity | Do not run many workers behind one User-Agent without external throttling — effective request rate scales with worker count |

Panel POST and batch ticker jobs should serialize fetches within each worker. Scale horizontally with dedicated SEC identities per worker, not by disabling or bypassing the client throttle.

## Request sizing

- **Panel POST:** maximum **25** tickers per request (422 if exceeded)
- Ticker routes fetch one filing per request; batch jobs should serialize or pool politely
- Large section text responses: use `include_text=false` on sections route unless needed

## Error handling

- **404** — filing not found; do not retry blindly with the same params
- **502** — upstream EDGAR failure; retry with backoff
- **422** — invalid client input
- Panel responses return per-ticker `status: error` without failing the whole request

## Security

- **No auth** in the API server — add API keys, mTLS, or VPN at your edge
- Do not expose unauthenticated instances to the public internet
- Scope claims: {doc}`../getting-started/scope-and-claims`

## Related

- {doc}`http/index` — HTTP API guide
- {doc}`../reference/http/endpoints` — endpoint reference
- {doc}`../getting-started/sec-edgar-setup`
