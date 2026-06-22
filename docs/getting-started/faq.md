# FAQ and Troubleshooting

Common questions when installing, scoring, or integrating Disclosure Alpha.

## Installation

**Q: `disclosure-alpha` command not found after pip install**

Use the same Python environment where you installed the package (`python3.11 -m pip install ...`). On some systems, scripts land in `~/.local/bin` — add that to your `PATH`.

**Q: Which extra do I need?**

| Goal | Install |
|------|---------|
| CLI + Python SDK only | `disclosure-alpha` |
| REST API | `disclosure-alpha[api]` |
| MCP for agents | `disclosure-alpha[mcp]` |
| API + MCP | `disclosure-alpha[api,mcp]` |

**Q: `pip install disclosure-alpha` fails with "No matching distribution"**

Requires **Python 3.11+**. On older Python versions PyPI will not offer a wheel. Contributors can install from source via {doc}`installation`.

## SEC EDGAR

**Q: Error about `SEC_USER_AGENT`**

SEC requires a descriptive User-Agent on every request:

```bash
export SEC_USER_AGENT="YourName your@email.com"
```

See {doc}`sec-edgar-setup`.

**Q: Requests fail or hang against EDGAR**

- Use a real name and email in `SEC_USER_AGENT`
- Respect rate limits; the client includes polite delays
- Cache repeat lookups with `DISCLOSURE_ALPHA_CACHE_DIR` (see {doc}`../reference/environment-variables`)

## Scoring output

**Q: How do I interpret 0–100 scores and component names?**

See {doc}`understanding-scores` for the score scale, plain-English component guide, and an annotated JSON walkthrough.

**Q: `disclosure_change_score` is `null`**

No prior comparable filing was available for that section. This is expected on a first filing or when `--prior-html` / `compare=prior` has no match — **null means missing**, not zero change.

**Q: Low `score_coverage_ratio` or many `missing_components`**

Required sections for the form type were not extracted (e.g. missing Item 7 MD&A on a 10-K). Check extraction with `disclosure-alpha extract` or the sections HTTP endpoint. Section names: {doc}`../reference/section-taxonomy`.

**Q: Scores differ from a previous run**

Compare `versions` in the JSON output (`parser_version`, `metrics_engine_version`, `scoring_model_version`, dictionary version). See {doc}`../reference/versioning`.

## HTTP API

**Q: Panel request returns `422`**

Maximum **25** tickers per panel POST. Split larger screens into batches.

**Q: Panel returns `status: error` for some tickers**

Panel requests do not fail-fast. Per-ticker errors (missing filing, bad ticker) appear in the response body while other tickers succeed.

**Q: Where is the OpenAPI spec?**

Start `disclosure-alpha-api`, then open `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/openapi.json`. See {doc}`../reference/http/openapi` and {doc}`../reference/http/endpoints`.

## MCP

**Q: Which MCP bundle should I use?**

| Bundle | When |
|--------|------|
| `disclosure-alpha-mcp-analyst` | Ticker discovery + scoring |
| `disclosure-alpha-mcp-builder` | Raw HTML pipeline control |

See {doc}`../guides/mcp/index` and {doc}`choose-your-surface`.

## Evidence and claims

**Q: Can I use scores as buy/sell signals?**

No. Scores summarize disclosure language and change — they are not investment advice and are not validated to predict returns. See {doc}`scope-and-claims` and {doc}`../legal`.

## Related

- {doc}`installation`
- {doc}`../guides/http/index`
- {doc}`../reference/environment-variables`
