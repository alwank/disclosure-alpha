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

Match language in [methodology/overview](methodology/overview.md) and [validation/evidence-and-limitations](validation/evidence-and-limitations.md):

- **Supported:** deterministic Item 1A on ~425 S&P 500 FY2025 10-Ks; partial L2 construct; partial L3 vol association
- **Do not claim:** full-index L2/L3 pass, earnings-surprise prediction, buy/sell signals, composite LLM scoring in OSS API

## Stub pages

Phase 2 pages contain ````{note} TODO` blocks. Replace the note with content; do not remove the page from the toctree.

## Local build

```bash
pip install -e ".[api,mcp,dev]"
pip install -r docs/requirements.txt
sphinx-build -W -b html docs docs/_build/html
```

CI runs the same command on every PR.

## Page template

New pages should follow [_templates/page_template.md](_templates/page_template.md): audience, prerequisites, summary, related links, artifact versions.
