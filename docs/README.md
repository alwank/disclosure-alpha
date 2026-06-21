# Documentation

The Disclosure Alpha documentation site is built with **Sphinx + MyST** (Material theme) and published on Read the Docs.

**Start here:** [index.md](index.md) (RTD home page)

## Local build

```bash
pip install -e ".[api,mcp,dev]"
pip install -r docs/requirements.txt
sphinx-build -W -b html docs docs/_build/html
open docs/_build/html/index.html
```

## Section map

| Section | Path | Audience |
|---------|------|----------|
| Getting Started | [getting-started/](getting-started/index.md) | Install, quickstarts, FAQ |
| Guides | [guides/](guides/index.md) | CLI, Python, HTTP, MCP, workflows |
| Reference | [reference/](reference/index.md) | Env vars, taxonomy, Python API, OpenAPI |
| Methodology | [methodology/](methodology/index.md) | How scoring works |
| Validation | [validation/](validation/index.md) | Evidence & limitations |
| Release notes | [appendix/changelog.md](appendix/changelog.md), [glossary](appendix/glossary.md) | Versions & terms |
| Legal | [legal.md](legal.md) | Disclaimer & license |

Contributor workflow: [CONTRIBUTING_DOCS.md](CONTRIBUTING_DOCS.md) (repo only; not in public nav).

Legacy numbered docs (`01_overview.md`–`09_product_surfaces.md`) redirect via sphinxext-rediraffe.
