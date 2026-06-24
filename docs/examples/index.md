# Examples Gallery

Copy-paste response shapes and API collections for integrators.

Regenerate JSON fixtures:

```bash
python scripts/generate_docs_examples.py
```

## Score responses

| Example | Workflow | File | Guide |
|---------|----------|------|-------|
| Minimal 10-K score | First CLI/Python/HTTP score | [`score-minimal-10k.json`](score-minimal-10k.json) | {doc}`../getting-started/first-successful-run` |
| Score with prior filing | Year-over-year change components | [`score-with-prior-snippet.json`](score-with-prior-snippet.json) | {doc}`../getting-started/understanding-scores` |
| Full coverage with prior | All nine headline components + prior; v2 cyber score when Item 1A incident language is present | [`score-full-coverage-snippet.json`](score-full-coverage-snippet.json) | {doc}`../reference/score-catalog` |
| Panel batch response | Multi-ticker HTTP screen | [`panel-response-snippet.json`](panel-response-snippet.json) | {doc}`../guides/workflows/index` |

`event_materiality_score` requires 8-K event sections (`item_1_01`, `item_1_05`, `item_2_02`, `item_5_02`, `item_8_01`) and stays **`null`** in the 10-K examples below.

### Minimal score (excerpt)

```{literalinclude} score-minimal-10k.json
:language: json
:lines: 124-145
```

### With prior filing (excerpt)

```{literalinclude} score-with-prior-snippet.json
:language: json
```

### Full coverage with prior (excerpt)

```{literalinclude} score-full-coverage-snippet.json
:language: json
```

### Panel response (excerpt)

```{literalinclude} panel-response-snippet.json
:language: json
```

## Postman collections

Product-oriented collections under [`docs/postman/`](https://github.com/alwank/disclosure-alpha/tree/main/docs/postman):

| Collection | Use when |
|------------|----------|
| `disclosure-alpha-discovery.postman_collection.json` | Health + filings |
| `disclosure-alpha-analytics.postman_collection.json` | Sections + metrics |
| `disclosure-alpha-scores.postman_collection.json` | Matrix tiers |
| `disclosure-alpha-compliance.postman_collection.json` | Flags + changes |
| `disclosure-alpha-panel.postman_collection.json` | Panel POST |
| `disclosure-alpha-api.postman_collection.json` | Full API |

Import into Postman or run via Newman. HTTP concepts: {doc}`../guides/http/index`. Endpoint reference: {doc}`../reference/http/endpoints`.

## Related

- {doc}`../getting-started/understanding-scores`
- {doc}`../reference/score-catalog`
- {doc}`../guides/workflows/index`
- {doc}`../reference/http/endpoints`
