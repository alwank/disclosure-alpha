# Contributing to Documentation

Disclosure Alpha docs are built with **Sphinx + MyST** and published on [Read the Docs](https://disclosure-alpha.readthedocs.io/en/latest/).

## Parallel ownership

Each section folder is owned by one workstream. Edit files **inside your section only** to avoid merge conflicts.

| Workstream | Folder | Owner focus |
|------------|--------|-------------|
| Getting Started | `getting-started/` | Install, quickstarts, concepts |
| Methodology | `methodology/` | Scoring specs, research, roadmap |
| Guides | `guides/` | CLI, HTTP, MCP, workflows |
| Reference | `reference/` | Env vars, taxonomy, autodoc, schemas |
| Validation | `validation/` | Evidence & limitations |
| Developer | `developer/`, `appendix/` | Architecture, testing, glossary |

**Do not edit** `docs/index.md` unless you are coordinating a release or adding a new top-level section. Section `index.md` files own their local toctrees.

## Link style

- Prefer MyST cross-references: `` {doc}`path/to/page` ``
- For anchors: `` {doc}`validation/evidence-and-limitations` ``
- External links: full URL with descriptive text
- Repo paths (e.g. `data/validation/`) use relative links from the doc file

## Claim boundaries

Match language in [scope-and-claims](getting-started/scope-and-claims.md) and [validation/evidence-and-limitations](validation/evidence-and-limitations.md):

- **Supported:** deterministic Item 1A on **428** S&P 500 FY2025 10-Ks (analysis cohort); partial L2 construct; partial L3 vol association (n=435)
- **Do not claim:** full-index L2/L3 pass, earnings-surprise prediction, buy/sell signals

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
