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
sphinx-build -E -W -b html docs docs/_build/html
```

Documentation-only edits: see [docs/CONTRIBUTING_DOCS.md](docs/CONTRIBUTING_DOCS.md).

## Claim boundaries

See `INTERNAL_VALIDATION.md` for the internal branch that hosts the full validation harness (scripts, reports, reproduction docs).

When writing docs or examples, match [Evidence and validation](https://disclosure-alpha.readthedocs.io/en/latest/getting-started/evidence.html) and [Scope and claims](https://disclosure-alpha.readthedocs.io/en/latest/getting-started/scope-and-claims.html):

- **Supported:** on **478** S&P 500 FY2025 Item 1A sections (`deterministic_scoring_v2`), company-specificity correlates **ρ ≈ 0.87** with an independent NER-based specificity measure
- **Do not claim:** full-index coverage, earnings-surprise prediction, buy/sell signals, or investment alpha

## Pull requests

1. Fork and branch from `main`
2. Keep changes focused
3. Ensure tests and docs build pass
4. Open a PR with a clear description of what changed and why

## Releasing

1. Bump `version` in `pyproject.toml` and the editable fallback in `src/disclosure_alpha/__init__.py` (kept in sync by `tests/test_version_sync.py`).
2. Update `docs/appendix/changelog.md`, `docs/getting-started/installation.md`, and `docs/reference/versioning.md` pins.
3. Regenerate committed doc artifacts if APIs or scoring output changed:
   ```bash
   python scripts/generate_http_endpoints_docs.py
   python scripts/generate_docs_examples.py
   ```
4. Run the CI-equivalent checks locally:
   ```bash
   pytest -q -m "not integration" --cov=disclosure_alpha --cov-fail-under=75
   pip install -r docs/requirements.txt
   python scripts/generate_http_endpoints_docs.py --check
   python scripts/generate_docs_examples.py --check
   sphinx-build -E -W -b html docs docs/_build/html
   ```
5. Merge to `main` — Read the Docs rebuilds [latest](https://disclosure-alpha.readthedocs.io/en/latest/) automatically.
6. Create a **published** GitHub Release with tag `vX.Y.Z` matching `pyproject.toml` — this triggers [`.github/workflows/publish.yml`](.github/workflows/publish.yml) (PyPI OIDC upload).
7. Verify PyPI install, API `info.version`, and RTD changelog/installation pins.
