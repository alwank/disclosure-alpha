# Contributing to Documentation

Disclosure Alpha docs are built with **Sphinx + MyST** and published on [Read the Docs](https://disclosure-alpha.readthedocs.io/en/latest/).

## Parallel ownership

Each section folder is owned by one workstream. Edit files **inside your section only** to avoid merge conflicts.

| Workstream | Folder | Owner focus |
|------------|--------|-------------|
| Getting Started | `getting-started/` | Install, quickstarts, concepts |
| Methodology | `methodology/` | Scoring specs, research, roadmap |
| Guides | `guides/` | CLI, HTTP, OpenBB, MCP, workflows |
| Reference | `reference/` | Env vars, taxonomy, autodoc, schemas |
| Developer | `developer/`, `appendix/` | Architecture, testing, glossary |

**Do not edit** `docs/index.md` unless you are coordinating a release or adding a new top-level section. Section `index.md` files own their local toctrees.

## Link style

- Prefer MyST cross-references: `` {doc}`path/to/page` ``
- For anchors: `` {doc}`getting-started/scope-and-claims` ``
- External links: full URL with descriptive text
- Repo paths (e.g. `data/validation/`) use relative links from the doc file

## Claim boundaries

Match language in [evidence](getting-started/evidence.md) and [scope-and-claims](getting-started/scope-and-claims.md):

- **Supported:** on **478** S&P 500 FY2025 Item 1A sections (`deterministic_scoring_v2`), company-specificity correlates **ρ ≈ 0.87** with an independent NER-based specificity measure
- **Do not claim:** full-index coverage, earnings-surprise prediction, buy/sell signals, or investment alpha

## Docs quality checks

```bash
pip install -e ".[api,mcp,dev]"
pip install -r docs/requirements.txt
python scripts/generate_http_endpoints_docs.py
sphinx-build -E -W -b html docs docs/_build/html
sphinx-build -b linkcheck docs docs/_build/linkcheck
rg -n "TODO|TBD|FIXME" docs --glob '!readthedocs-public-docs-improvement-plan.md'
```

CI runs HTML build and placeholder scan on every PR.

## Page template

New pages should follow [_templates/page_template.md](_templates/page_template.md): audience, prerequisites, summary, related links, artifact versions.
