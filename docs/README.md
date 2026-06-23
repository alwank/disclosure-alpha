# Documentation

The Disclosure Alpha documentation site is built with **Sphinx + MyST** (Material theme) and published on Read the Docs.

**Start here:** [index.md](index.md) (RTD home page)

## Local build

```bash
pip install -e ".[api,mcp,dev]"
pip install -r docs/requirements.txt
python scripts/generate_http_endpoints_docs.py
sphinx-build -E -W -b html docs docs/_build/html
open docs/_build/html/index.html
```

## Section map

| Section | Path | Audience |
|---------|------|----------|
| Start Here | [getting-started/](getting-started/index.md) | Install, first run, scope, evidence, FAQ |
| Guides | [guides/](guides/index.md) | CLI, Python, HTTP, MCP, workflows, production |
| Examples | [examples/](examples/index.md) | JSON fixtures, Postman collections |
| Reference | [reference/](reference/index.md) | Env vars, versioning, Python API, HTTP endpoints |
| Methodology | [methodology/](methodology/index.md) | How scoring works |
| Release notes | [appendix/changelog.md](appendix/changelog.md), [glossary](appendix/glossary.md) | Versions & terms |
| Legal | [legal.md](legal.md) | Disclaimer & license |

Contributor workflow: [CONTRIBUTING_DOCS.md](CONTRIBUTING_DOCS.md) (repo only; excluded from public RTD build).

Legacy numbered docs (`01_overview.md`–`09_product_surfaces.md`) redirect via sphinxext-rediraffe.
