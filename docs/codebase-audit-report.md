# Disclosure Alpha - Codebase Audit Report

**Date:** June 2026  
**Scope:** Full project scan — inconsistencies, dead code, stale code, documentation gaps, technical debt

## Executive Summary

Disclosure Alpha is in **good overall health**: 231 unit tests pass at **81.8% coverage** (above the 75% gate), Sphinx builds with `-W`, and the core pipeline is well-tested. The main risks are **version drift** across four surfaces, **overstated 8-K / EDGAR support** in public docs, and a handful of **orphaned or low-coverage modules** (`filing_normalizer.py`, EDGAR client/resolver, embedding backend). Documentation is substantially improved (June 2026 RTD work), but README examples and the improvement-plan file still lag reality.

---

## 1. Inconsistencies

### High

| # | Location | Description | Suggested fix |
|---|----------|-------------|---------------|
| 1 | `pyproject.toml:7`, `src/disclosure_alpha/__init__.py:49`, `src/disclosure_alpha/api/app_factory.py:12`, `docs/conf.py:15` | **Package version triple mismatch**: PyPI/changelog = `1.1.0`, `__version__` = `1.0.1`, FastAPI app = `1.0.0`. RTD `release` reads stale `__version__`. | Single source of truth: `importlib.metadata.version("disclosure-alpha")` in `__init__.py`; re-export to FastAPI and docs. |
| 2 | `README.md:136`, `src/disclosure_alpha/version.py:1`, `docs/reference/versioning.md:10` | README example JSON shows `"parser_version": "sec_parser_v1"`; runtime and docs use `section_extractor_v1`. | Fix README example to match `PARSER_VERSION`. |
| 3 | `docs/getting-started/scope-and-claims.md:9`, `docs/index.md:50`, `src/disclosure_alpha/edgar/resolver.py:22-26` | Docs claim **10-K, 10-Q, and 8-K** support. EDGAR resolver only accepts `10-K` / `10-Q` (`normalize_form_type` raises on 8-K). 8-K works for **local HTML** only. | Narrow claims: "8-K supported for local HTML / MCP Builder extraction; ticker/EDGAR routes are 10-K/10-Q only." Or add 8-K to resolver. |
| 4 | `docs/getting-started/installation.md:22` | Pins `disclosure-alpha==1.0.1[api,mcp]` while `pyproject.toml` is `1.1.0`. | Update pin to `1.1.0` or use a version-agnostic example. |

### Medium

| # | Location | Description | Suggested fix |
|---|----------|-------------|---------------|
| 5 | `README.md:86`, `src/disclosure_alpha/api/endpoints/matrix.py:40-43`, `src/disclosure_alpha/api/endpoints/panel.py` | README says HTTP matrix supports `tier=lite|standard|analyst`. **`tier` exists only on GET** `/v1/company/{ticker}/disclosure-matrix`. Panel POST has `include`/`fields` but no `tier`. Docs HTTP guide documents this ("matrix only") but README does not. | Add "(single-ticker GET only)" to README or add `tier` to `PanelRequest`. |
| 6 | `src/disclosure_alpha/filing_normalizer.py` vs `src/disclosure_alpha/edgar/resolver.py:22-26` | Duplicate form-normalization logic: `parse_filing_type()` in normalizer vs `normalize_form_type()` in resolver. Only resolver is used. | Delete `filing_normalizer.py` or wire it in and dedupe. |
| 7 | `src/disclosure_alpha/mcp/analyst.py:23-34` vs `src/disclosure_alpha/mcp/builder.py:25`, `src/disclosure_alpha/mcp/tools.py:38` | Analyst MCP docstrings say **10-K / 10-Q only**; Builder/tools mention **8-K**. Surfaces disagree on form scope. | Align docstrings with actual supported forms per bundle. |
| 8 | `src/disclosure_alpha/cli.py:40` | CLI `--form` help says "10-K or 10-Q" but scoring pipeline can accept 8-K HTML. | Update help text or explicitly reject unsupported forms at CLI boundary. |
| 9 | Multiple API files | Legacy **"Track A/B/C/D/E"** ownership comments (`api/endpoints/flags.py:1`, `api/schemas/panel.py:1`, etc.) from an old work-split. | Remove or replace with module-level docstrings. |

### Low

| # | Location | Description | Suggested fix |
|---|----------|-------------|---------------|
| 10 | `pyproject.toml:47-49`, `docs/guides/mcp/index.md:14` | Three MCP entry points (`disclosure-alpha-mcp`, `-analyst`, `-builder`) plus legacy alias. Intentional but easy to confuse. | README already documents this; consider deprecating `disclosure-alpha-mcp` in a future major. |
| 11 | `src/disclosure_alpha/api/routes.py` + `app_factory.py` | App created via factory; `routes.py` is a thin backward-compat shim. Fine, but two module paths (`api.routes:app` vs `create_app()`). | Document canonical import path in contributor docs. |
| 12 | `docs/reference/section-taxonomy.md` vs `src/disclosure_alpha/dictionaries.py:354-368` | Taxonomy lists 5 8-K sections; `REQUIRED_SECTIONS["8-K"]` only requires `item_2_02`. | Add a "required for scoring" column to 8-K table. |

---

## 2. Dead Code / Unused Code

### High

| # | Location | Description | Suggested fix |
|---|----------|-------------|---------------|
| 1 | `src/disclosure_alpha/filing_normalizer.py` (entire file, 0% coverage) | **Zero imports** anywhere in repo. `parse_filing_type()` and `sic_to_sector()` are orphaned. | Delete file or integrate `sic_to_sector` if product needs sector metadata. |

### Medium

| # | Location | Description | Suggested fix |
|---|----------|-------------|---------------|
| 2 | `pyproject.toml:42` | **`pytest-asyncio`** declared in `[dev]` but no `async def` tests exist. | Remove from dev extras unless async tests are planned. |
| 3 | `pyproject.toml:42` | **`httpx2`** in dev deps; tests use `fastapi.testclient.TestClient` (Starlette), not httpx2 directly. | Remove httpx2 or add tests that use it. |
| 4 | `src/disclosure_alpha/mcp/server.py:6-14` | Re-exports tools (`compute_section_metrics_tool`, etc.) that are **never imported** externally; only `main` is used via entry point. | Trim unused re-exports or document as public API. |
| 5 | `src/disclosure_alpha/api/app.py` | `main()` has **0% test coverage** (uvicorn bootstrap only). Marked `# pragma: no cover` partially but whole file shows 0%. | Add `# pragma: no cover` to entire module or a smoke test. |

### Low

| # | Location | Description | Suggested fix |
|---|----------|-------------|---------------|
| 6 | `src/disclosure_alpha/mcp/__init__.py` | Empty package init. | Fine as-is; no action needed. |
| 7 | `docs/_build/` (local) | Build artifacts present locally but **gitignored** (`.gitignore:14`). Not dead code, but clutters workspace searches. | `rm -rf docs/_build` locally; already ignored in CI. |

---

## 3. Stale Code

### High

| # | Location | Description | Suggested fix |
|---|----------|-------------|---------------|
| 1 | `docs/readthedocs-public-docs-improvement-plan.md:28-29` | Plan still claims `docs/developer/architecture.md` and `testing.md` contain **TODO/TBD** placeholders. Those pages were rewritten (no TODOs). Plan header says "implemented" but body is stale. | Archive plan or update "Current State" to reflect June 2026 completion. |
| 2 | `docs/methodology/roadmap/v2-improvement-plan.md:28-49` | References `--phase deterministic`, `view=deterministic`, and pre-1.1 API shapes removed in changelog. | Mark historical items done; remove `view` references. |

### Medium

| # | Location | Description | Suggested fix |
|---|----------|-------------|---------------|
| 3 | `docs/methodology/roadmap/v2-improvement-plan.md` (entire dir) | Excluded from public RTD (`docs/conf.py:46`) but contains outdated product assumptions. | Keep excluded; add "internal/historical" note at top. |
| 4 | `src/disclosure_alpha/filing_normalizer.py:1` | Docstring references **"Doc 02"** — internal design doc naming with no repo artifact. | Remove with file, or update docstring. |
| 5 | `src/disclosure_alpha/text_metrics.py:123` | Docstring **"per Doc 04"** — same internal-doc pattern. | Replace with plain description. |
| 6 | `pyproject.toml:47` | `disclosure-alpha-mcp` legacy entry point kept for backward compat. | Document deprecation timeline in changelog. |

### Low

| # | Location | Description | Suggested fix |
|---|----------|-------------|---------------|
| 7 | `docs/developer/index.md:3` | Says section is **"under development"** but `developer/**` is excluded from public RTD build anyway. | Low priority; contributor-only. |
| 8 | `src/disclosure_alpha/section_extractor.py:144` | Bare `except Exception:` when loading sec_parser — swallows all errors silently. | Catch `ImportError` / specific exceptions; log or warn. |

---

## 4. Documentation Inconsistencies

### High

| # | Location | Description | Suggested fix |
|---|----------|-------------|---------------|
| 1 | `README.md:136` vs `docs/examples/score-minimal-10k.json:12` | Wrong `parser_version` in README hero example (see §1). | Sync README JSON with generated examples. |
| 2 | `docs/getting-started/scope-and-claims.md:9` vs resolver | **8-K overclaim** for ticker/EDGAR workflows (see §1). | Add explicit surface matrix (CLI `--html` vs `--ticker`, HTTP, MCP). |
| 3 | `docs/getting-started/installation.md:22` | Version pin `1.0.1` vs package `1.1.0`. | Update pin. |

### Medium

| # | Location | Description | Suggested fix |
|---|----------|-------------|---------------|
| 4 | `docs/readthedocs-public-docs-improvement-plan.md` vs `docs/conf.py:33-48` | Plan says hidden toctree in `docs/index.md` exposes contributor pages publicly. **`developer/**` and `CONTRIBUTING_DOCS.md` are now excluded** from build; issue largely resolved. | Close plan item R1 as done. |
| 5 | `README.md:97` vs `docs/guides/http/index.md:60` | README mentions tiers without "matrix only" qualifier. | Cross-link HTTP guide tier section. |
| 6 | `docs/reference/environment-variables.md:6` | Documents `DISCLOSURE_ALPHA_CACHE_DIR` as functional. Code **does** use it via `edgar/resolver.py` → `edgar/cache.py`. Accurate, but no user-facing confirmation cache is on by default. | Add one-line note in SEC setup guide that caching is automatic. |
| 7 | `docs/conf.py:127` | Redirect `reference/oss-score-catalog.md` → `score-catalog.md` but source OSS file is gone. Redirect is harmless; stale `_build` may still show old page locally. | No action if OSS file deleted intentionally. |

### Low

| # | Location | Description | Suggested fix |
|---|----------|-------------|---------------|
| 8 | `README.md` vs `README-PYPI.md` | GitHub README is richer; PyPI readme is abbreviated (intentional per `pyproject.toml:9`). | Periodic sync of version claims and quick-start. |
| 9 | External linkcheck | CI ignores DOI/SEC/MCP redirects (`docs/conf.py:51-57`). Known limitation, documented in improvement plan. | Accept or add allowlist comments in CI. |

---

## 5. Technical Debt

### High

| # | Location | Description | Suggested fix |
|---|----------|-------------|---------------|
| 1 | `src/disclosure_alpha/edgar/client.py:14-15` | **Global throttle lock** (`_last_request_at`) is process-wide and not thread-safe for multi-worker API deployments. | Per-worker is OK for single-process; document "one worker per SEC identity" or use threading lock. |
| 2 | `src/disclosure_alpha/edgar/client.py` (33%), `edgar/resolver.py` (32%) | EDGAR layer has **low unit-test coverage**; most paths only hit integration/EDGAR smoke. | Add mocked resolver/client unit tests (no network). |
| 3 | `pyproject.toml:59-61` | **`validation/*` omitted from coverage** entirely. Validation logic tested only via `test_construct_validity.py` / scripts. | Include validation in coverage or add targeted unit tests. |
| 4 | `src/disclosure_alpha/pipeline.py:455` | `score_panel_tickers` catches bare **`except Exception`** — masks bugs as per-ticker errors. | Catch `EdgarError`, `ValueError`, etc.; let unexpected exceptions propagate. |

### Medium

| # | Location | Description | Suggested fix |
|---|----------|-------------|---------------|
| 5 | `src/disclosure_alpha/embedding_service.py` (36% cov) | Semantic path uses optional `sentence-transformers`; failures fall back to TF-IDF silently (`except Exception`). | Log fallback once; document `[semantic]` extra. |
| 6 | `src/disclosure_alpha/cli.py` (61% cov) | `extract` and `metrics` subcommands less tested than `score`. | Add `test_cli.py` cases for extract/metrics branches. |
| 7 | `src/disclosure_alpha/mcp/analyst.py` (72%), `builder.py` (71%) | MCP `main()` entry points partially untested. | Smoke-test `main` with mocked `mcp.run`. |
| 8 | `docs/guides/production.md:7-13` | API binds **`0.0.0.0:8000` by default** with no auth. Documented, but easy to misdeploy. | Production guide is good; consider defaulting to `127.0.0.1` (breaking change). |
| 9 | `pyproject.toml:25` | **`sec-parser` pinned** to `<0.59` — tight coupling; upstream breakage risk. | Monitor sec-parser releases; add compatibility test. |
| 10 | `.github/workflows/ci.yml:37-39` | Dictionary shift validation is **non-blocking** (`continue-on-error: true`). | Make blocking once stable, or document why it stays advisory. |

### Low

| # | Location | Description | Suggested fix |
|---|----------|-------------|---------------|
| 11 | No `ruff` / `mypy` / `black` in CI | Linting/type-checking not enforced. | Add ruff if team wants style gates. |
| 12 | `src/disclosure_alpha/section_extractor.py` (~449 lines) | Large module with multiple extraction strategies. Works, but high complexity. | Future refactor only if extraction changes are frequent. |
| 13 | `numpy` base dependency | Used by `embedding_service` (core diff path) and validation. Reasonable, but pulls numpy for all installs. | Acceptable for analytics package. |

---

## Priority Action Items

| Rank | Item | Impact | Effort | Notes |
|------|------|--------|--------|-------|
| 1 | **Unify version to 1.1.0** (`__init__.py`, FastAPI, installation docs) | High | **S** | Blocks correct RTD release label and PyPI trust |
| 2 | **Fix README `parser_version` example** | High | **S** | One-line JSON fix |
| 3 | **Clarify 8-K support scope** in scope-and-claims, README, index | High | **S** | Doc-only unless adding EDGAR 8-K |
| 4 | **Delete `filing_normalizer.py`** (or wire it in) | Medium | **S** | 0% coverage, zero imports |
| 5 | **Update `installation.md` version pin** to 1.1.0 | Medium | **S** | |
| 6 | **Archive/update RTD improvement plan** stale observations | Medium | **S** | Reduces contributor confusion |
| 7 | **Add mocked EDGAR unit tests** for resolver/client | High | **M** | Biggest coverage gap in core package |
| 8 | **Narrow `score_panel_tickers` exception handling** | Medium | **S** | Safer batch API behavior |
| 9 | **Remove unused dev deps** (`pytest-asyncio`, `httpx2`) | Low | **S** | Cleaner install |
| 10 | **Add CLI tests** for `extract` / `metrics` commands | Medium | **S** | Raises cli.py from 61% |
| 11 | **Document SEC throttle / single-worker guidance** for production API | Medium | **S** | production.md extension |
| 12 | **Align MCP Analyst docstrings** with 8-K reality | Low | **S** | |
| 13 | **Clean v2 roadmap** of `view=` / `--phase` references | Low | **S** | |
| 14 | **Consider `tier` on panel POST** or explicit README note | Low | **S–M** | API design choice |
| 15 | **Thread-safe EDGAR throttle** if multi-worker deployment is a goal | Medium | **M** | Only if scaling API |

---

## Appendix

### Files / directories scanned

- **Source:** `src/disclosure_alpha/` (59 Python modules)
- **Tests:** `tests/` (23 test files)
- **Scripts:** `scripts/` (11 files)
- **Docs:** `docs/` (excluding `docs/_build/`, which is gitignored)
- **CI/Config:** `.github/workflows/ci.yml`, `integration.yml`, `publish.yml`, `pyproject.toml`, `docs/conf.py`, `CONTRIBUTING.md`, `SECURITY.md`
- **Data:** `data/validation/` (reports referenced, not fully audited)

### Tools / commands used

```bash
source .venv/bin/activate
pip install -e ".[api,mcp,dev]"
python3 -m pytest -q -m "not integration" --cov=disclosure_alpha --cov-report=term-missing
sphinx-build -E -W -b html docs docs/_build/html
python scripts/generate_docs_examples.py --check
rg -n "TODO|FIXME|HACK|XXX|TBD|deprecated" src scripts tests
rg -n "TODO|TBD|FIXME" docs --glob '!readthedocs-public-docs-improvement-plan.md' --glob '!_build/**'
```

### Limitations of this scan

1. No static dead-code analyzer (vulture, pylint unused-import) was run.
2. Integration / EDGAR tests not executed (require `RUN_INTEGRATION=1`, `SEC_USER_AGENT`, network).
3. `validation/` package excluded from coverage metrics.
4. Runtime security (dependency CVEs) not scanned.
5. PyPI published artifact not inspected.
6. Linkcheck not re-run.
7. Commented-out code blocks — minimal in `src/`.
8. Local `docs/_build/` artifacts may inflate Glob counts but are not in git.

---

**Bottom line:** Ship a small **version + README + 8-K scope** cleanup first (all **S** effort). The codebase is maintainable and well-tested for its core deterministic pipeline; the largest engineering gap is **EDGAR layer test coverage** and **honest form-type documentation** across surfaces.
