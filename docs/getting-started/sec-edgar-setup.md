# SEC EDGAR Setup

SEC fair-access policy requires a descriptive `User-Agent` header on all EDGAR requests. Disclosure Alpha reads this from the environment and optionally caches filings on disk.

## User-Agent (required)

```bash
export SEC_USER_AGENT="YourName your@email.com"
```

Use your real name and contact email. Requests without a proper User-Agent may be blocked.

## Cache directory (optional)

Default cache path: `data/cache/sec_filings`

```bash
export DISCLOSURE_ALPHA_CACHE_DIR="/path/to/cache"
```

Cached filings speed up repeat lookups.

## Fair access

- Respect SEC rate limits; the client includes polite delays.
- Do not distribute bulk-scraped filings without reviewing SEC terms of use.
- For production deployments, set `SEC_USER_AGENT` in the process environment for the HTTP API or MCP server.

See {doc}`../reference/environment-variables` for all configuration options.

## Related

- {doc}`quickstart-cli`
- {doc}`quickstart-python`
- {doc}`../guides/http/index`
