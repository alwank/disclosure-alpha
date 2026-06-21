# Contributing to Disclosure Alpha

Thanks for your interest in contributing. Disclosure Alpha is Apache-2.0 licensed.

## Install for development

Clone the repository and install in editable mode:

```bash
git clone https://github.com/alwank/disclosure-alpha.git
cd disclosure-alpha
pip install -e ".[api,mcp,dev]"
```

End users install from PyPI instead: `pip install "disclosure-alpha[api,mcp]"`. See [Installation](https://disclosure-alpha.readthedocs.io/en/latest/getting-started/installation.html).

## Run tests

```bash
pytest -q -m "not integration" --cov=disclosure_alpha --cov-fail-under=75
```

Integration tests (network / EDGAR):

```bash
RUN_INTEGRATION=1 pytest -q -m integration
```

Set `SEC_USER_AGENT="YourName your@email.com"` for EDGAR-backed tests.

## Build docs locally

```bash
pip install -r docs/requirements.txt
sphinx-build -W -b html docs docs/_build/html
```

Documentation-only edits: see [docs/CONTRIBUTING_DOCS.md](docs/CONTRIBUTING_DOCS.md).

## Claim boundaries

When writing docs or examples, match [Evidence & limitations](https://disclosure-alpha.readthedocs.io/en/latest/validation/evidence-and-limitations.html):

- **Supported:** deterministic Item 1A on ~425 S&P 500 FY2025 10-Ks; partial L2 construct validity; partial L3 volatility association
- **Do not claim:** full-index validation, earnings-surprise prediction, buy/sell signals, or composite LLM scoring in the open-source API

## Pull requests

1. Fork and branch from `main`
2. Keep changes focused
3. Ensure tests and docs build pass
4. Open a PR with a clear description of what changed and why
