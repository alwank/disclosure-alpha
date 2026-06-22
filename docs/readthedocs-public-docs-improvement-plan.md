# Read the Docs Public Documentation Improvement Plan

> **Archive — do not treat as an active backlog.** June 2026 implementation is complete. Remaining gaps are tracked in [codebase-audit-report](codebase-audit-report.md).

Audit date: 2026-06-22 · Archived: 2026-06-23

Scope (original): public Read the Docs experience for Disclosure Alpha — `docs/index.md`, Getting Started, Guides, Reference, Methodology, Validation, Legal, RTD build config.

This file is excluded from the public RTD build (`docs/conf.py`). The sections below preserve the original audit and plan for context; status markers reflect what shipped on `main`.

## Implementation rollup (June 2026)

| Area | Outcome |
|------|---------|
| Public hygiene (R1, R3) | Contributor/developer pages excluded from RTD; composite/OSS scope notes removed |
| Onboarding (A1–A3) | {doc}`getting-started/first-successful-run`, {doc}`getting-started/scope-and-claims`, {doc}`examples/index` in public nav |
| Integration reference (A4–A6) | {doc}`reference/http/endpoints`, {doc}`reference/versioning`, {doc}`guides/production` |
| CI docs gates (A7) | `sphinx-build -E -W` and linkcheck in `.github/workflows/ci.yml` |
| Endpoint/schema stubs (R2) | Placeholder trees under `guides/http/endpoints/` and `reference/http/schemas/` removed |
| Claim centralization | Validation counts in {doc}`validation/evidence-and-limitations` and {doc}`getting-started/scope-and-claims` |

## Final state (June 2026)

- `sphinx-build -E -W -b html docs docs/_build/html` passes and generates **52** public pages.
- `sphinx-build -b linkcheck` runs in CI; `linkcheck_ignore` in `docs/conf.py` documents bot-blocked DOI/SEC/MCP URLs.
- `docs/conf.py` excludes `developer/**`, `CONTRIBUTING_DOCS.md`, and this plan from the public build.
- `docs/developer/architecture.md` and `docs/developer/testing.md` are contributor-facing pages **without** `TBD` / `TODO` placeholders.
- Public-build pages contain no accidental `TODO` / `TBD` (verified via `rg` in CI contributor docs).
- Validation numbers are centralized (n=428 construct validity; n=435 volatility cohort).
- Score catalog lives at {doc}`reference/score-catalog`; disclaimer duplication trimmed via scope/evidence cross-links.

## Original executive summary (June 2026 audit)

At audit time the docs were structurally usable but needed audience separation, claim hygiene, first-run confidence, and less overexposed implementation detail. Highest-impact items (all implemented):

1. Remove hidden public pages meant for contributors or developer placeholders.
2. Add a stronger "happy path" onboarding flow with expected outputs and troubleshooting checkpoints.
3. Centralize validation claims so README, docs, changelog, and contributor guidance do not drift.
4. Add public API examples generated from the real OpenAPI schema instead of maintaining placeholder endpoint/schema pages.
5. Trim repeated "not supported / no LLM" language into one canonical limitation block and link to it (`scope-and-claims`, `evidence-and-limitations`).

## Audience Model

Public docs should prioritize these audiences in order:

1. Evaluators: people deciding whether to trust and try the package.
2. First-time users: people installing and scoring one filing.
3. Integrators: people wiring CLI, Python, HTTP, or MCP into workflows.
4. Auditors/researchers: people checking methodology, evidence, and limitations.
5. Contributors: people modifying the repo.

Read the Docs should primarily serve audiences 1-4. Contributor-only docs can live in the repo, but should not be built into the public RTD site unless they are complete and intentionally surfaced.

## ADD

### A1. Add a "First Successful Run" page — **done (2026-06)**

Create `docs/getting-started/first-successful-run.md` and add it near the top of `docs/getting-started/index.md`.

Purpose: reduce time-to-value for public users.

Content:

- Python version check.
- Install command.
- `SEC_USER_AGENT` setup.
- One local HTML path that does not require EDGAR.
- One ticker path that does require EDGAR.
- Expected JSON fields and a small expected output block.
- "If this fails" table with command-not-found, missing user agent, filing not found, and low coverage.

Why: the current docs split install, EDGAR setup, CLI quickstart, Python quickstart, score interpretation, and FAQ. That is clean reference structure, but a first-time public user needs one complete path that proves the package works.

Acceptance criteria:

- A new user can run one command sequence without opening more than one other page.
- The page links to full CLI/Python guides after success, not before.
- The page uses a stable fixture or local HTML example where possible.

### A2. Add a public "What This Does and Does Not Claim" page — **done (2026-06)**

Create `docs/getting-started/scope-and-claims.md` or expand `docs/validation/evidence-and-limitations.md` into a more user-facing canonical page.

Content:

- Supported product claims.
- Unsupported claims.
- Validation cohort and exact count source.
- Difference between language signal, risk score, and investment signal.
- Meaning of deterministic and "no LLM required."

Why: the docs currently state limitations in several places. A canonical page will reduce duplication and make public claims easier to audit.

Acceptance criteria:

- README, RTD index, methodology overview, FAQ, HTTP guide, legal page, and contributor docs link to this page instead of repeating full disclaimers.
- Validation counts are pulled from one source of truth or copied from one explicitly named report.

### A3. Add an "Examples Gallery" page — **done (2026-06)**

Create `docs/examples/index.md` and include it in the public nav, while continuing to exclude raw JSON files from page rendering if desired.

Content:

- One-card list of example artifacts:
  - minimal score response
  - score with prior response
  - panel response
  - Postman collections
- For each example:
  - what workflow it supports
  - linked file path
  - related guide

Why: examples currently exist as files and literalincludes, but there is no public landing page for users who want copy-paste payloads and response shapes.

Acceptance criteria:

- `docs/examples/score-minimal-10k.json`, `score-with-prior-snippet.json`, and `panel-response-snippet.json` are discoverable from RTD navigation.
- HTTP guide and workflows link to the gallery.

### A4. Add real HTTP endpoint reference generated from FastAPI/OpenAPI — **done (2026-06)**

Replace the excluded endpoint stubs with generated or semi-generated endpoint reference.

Recommended approach:

- Keep `docs/guides/http/index.md` as the conceptual guide.
- Add `docs/reference/http/endpoints.md` generated from `openapi.json` during docs build or via a committed script.
- Include:
  - method and path
  - query/body params
  - response model
  - common errors
  - one curl example per endpoint

Why (original): placeholder endpoint stubs existed; public integrators needed endpoint-level details that match the running app. Stubs were removed; {doc}`reference/http/endpoints` is the canonical reference.

Acceptance criteria:

- No endpoint reference page contains `TBD` or `TODO`.
- Endpoint docs are generated from or checked against the live FastAPI schema.
- The generated reference is linked from `docs/reference/http/openapi.md`.

### A5. Add a "Versioning and Reproducibility" page — **done (2026-06)**

Create `docs/reference/versioning.md`.

Content:

- Package version vs parser version vs metrics version vs dictionary version vs scoring model version.
- How to pin `disclosure-alpha==1.0.1`.
- What changes can alter scores.
- How to record versions from JSON output.
- Where validation reports live.

Why: version strings are mentioned across understanding scores, methodology, changelog, validation, and glossary. Public users evaluating reproducibility need one reference.

Acceptance criteria:

- Install docs link to versioning from "Pin a release."
- Methodology and validation pages link to versioning instead of duplicating artifact tables.

### A6. Add a "Production Notes" page for hosted use — **done (2026-06)**

Create `docs/guides/production.md` or `docs/guides/deployment.md`.

Content:

- Running `disclosure-alpha-api` behind a service layer.
- Required environment variables.
- SEC fair-access expectations.
- Cache directory.
- Request sizing and panel limit.
- Error handling.
- No authentication is provided by the local API server unless the integrator adds it.

Why: public HTTP API docs show local startup, but integrators will ask what is safe to expose or deploy.

Acceptance criteria:

- HTTP guide links to production notes.
- Legal page links to production notes for EDGAR usage and redistribution caveats.

### A7. Add docs quality checks to CI or contributor workflow — **done (2026-06)**

Add or document a docs-check command that runs:

```bash
sphinx-build -E -W -b html docs docs/_build/html
sphinx-build -b linkcheck docs docs/_build/linkcheck
rg -n "TODO|TBD|FIXME" docs
```

For linkcheck, add `linkcheck_ignore` entries in `docs/conf.py` for links that reliably block automated clients, such as DOI resolver targets or SEC pages, while preserving human-facing links.

Why: public docs should not regress silently when hidden pages or placeholders are added.

Acceptance criteria:

- HTML build remains warning-free.
- Linkcheck has either clean output or documented ignores for known bot-blocked sources.
- Public-build pages contain no accidental `TODO` / `TBD`.

## REMOVE

### R1. Remove contributor/developer hidden pages from the public build — **done (2026-06-22)**

Edit `docs/index.md` and remove this hidden toctree from public docs:

```text
CONTRIBUTING_DOCS
developer/architecture
developer/testing
```

Options:

- Keep these files in the repo but exclude them from Sphinx with `exclude_patterns`.
- Move them under a repo-only folder such as `docs-internal/`.
- Publish them only after they contain complete public-grade content.

Why: hidden pages still generate public URLs and can appear in search. Two of the three currently contain placeholder content.

Acceptance criteria:

- Fresh Sphinx build no longer reads `CONTRIBUTING_DOCS`, `developer/architecture`, or `developer/testing`.
- `docs/README.md` remains the repo-facing docs contributor entry point.

### R2. Remove placeholder endpoint/schema pages unless they are actively generated — **done (2026-06)**

Placeholder trees (`docs/guides/http/endpoints/`, `docs/reference/http/schemas/`) were deleted. Endpoint reference lives at {doc}`reference/http/endpoints`.

### R3. Remove unsupported-product emphasis from high-traffic pages — **done (2026-06-22)**

Composite/OSS scope notes removed from FAQ, glossary, scope-and-claims, HTTP guide, and evidence pages. README and RTD index emphasize supported deterministic workflows only.

### R4. Remove source-code file path references from public narrative pages where they are not needed

Keep source paths in reference and contributor docs, but trim from user-facing guides.

Examples:

- `src/disclosure_alpha/pipeline.py` in methodology overview can move to Python/reference or architecture docs.
- `src/disclosure_alpha/dictionaries.py` in research foundation can be softened to "the built-in dictionary module" unless the reader is in reference docs.

Why: public evaluator and onboarding pages should explain behavior before repository internals.

Acceptance criteria:

- Getting Started and Guides pages avoid source paths unless the user must open the source.
- Methodology keeps source paths only where they clarify reproducibility.

## TRIM

### T1. Trim duplicated disclaimers into short callouts

Current repeated themes:

- Not investment advice.
- Not a trading signal.
- No LLM required.
- Validation not full-index and not earnings-surprise supported.

Plan:

- Use one short disclaimer block on `docs/index.md`.
- Use one canonical page for full scope and limitations.
- Replace repeated paragraphs elsewhere with one-line cross-links.

Why: public docs need strong claim boundaries, but repetition makes the docs feel defensive and harder to scan.

Acceptance criteria:

- Each major guide has at most one short scope note.
- Full details live in validation/legal/scope pages.

### T2. Trim the public nav to user journeys

Current nav sections are reasonable, but the first-level public journey can be sharper.

Recommended public nav order:

1. Start Here
2. Guides
3. Examples
4. Reference
5. Methodology
6. Evidence and Limitations
7. Legal

Changes:

- Rename "Getting Started" to "Start Here" if the theme/sidebar supports it cleanly.
- Add Examples.
- Keep Changelog and Glossary under Reference or Appendix, not as a prominent release-notes section unless releases become a key public workflow.

Why: public readers usually want "try it", "integrate it", "trust it", then "look up details."

Acceptance criteria:

- Home page "Start here" table maps directly to nav sections.
- Appendix does not compete with core user docs.

### T3. Trim deep methodology pages for public readability

Keep the specifications, but make the top of each page more scannable.

Targets:

- `docs/methodology/metrics-engine.md`
- `docs/methodology/diff-engine.md`
- `docs/methodology/aggregation.md`

Plan:

- Add a 5-line "What this page answers" block.
- Move detailed formulas below examples.
- Keep tables, but reduce repeated field definitions that already live in reference/glossary.

Why: methodology is important for trust, but public users should understand the main behavior before formulas.

Acceptance criteria:

- Each methodology spec begins with purpose, inputs, outputs, and version.
- Formula-heavy sections remain available but not first-screen dominant.

### T4. Trim README vs RTD overlap

README should stay a product landing page and installation entry point. RTD should carry deeper instructions.

Plan:

- Keep README quick start, capabilities, examples, and docs links.
- Move detailed MCP config and repeated research/validation tables to RTD links, or keep them shorter.
- Ensure README and `docs/index.md` do not compete with different "start here" maps.

Why: public users often start on GitHub, then move to RTD. They should not have to reconcile two versions of the same docs.

Acceptance criteria:

- README links to RTD for details after a short working example.
- RTD home page remains the canonical docs table of contents.

### T5. Trim unreleased or roadmap material from public docs

Current excluded roadmap files are not built, which is good. Keep that boundary.

Plan:

- Keep `docs/methodology/roadmap/**` excluded unless publishing an explicit public roadmap.
- Document present-tense product behavior only; composite/OSS scope notes removed (2026-06-22).

Why: public docs should document what exists now. Future plans create support expectations.

Acceptance criteria:

- Public docs use present-tense product behavior.
- Future-looking language is isolated to changelog or a clearly labeled roadmap if one is intentionally published.

## File-Level Action Plan

### `docs/index.md`

- Add link to "First Successful Run."
- Keep the start table, but add "I am evaluating whether to trust this" -> scope/evidence page.
- Remove hidden contributor/developer toctree.
- Keep only a short legal/scope sentence.

### `docs/getting-started/index.md`

- Add `first-successful-run`.
- Add `scope-and-claims` if created under Getting Started.
- Consider placing `understanding-scores` before deep concepts.

### `docs/getting-started/installation.md`

- Add "After install, run this exact command" link to first successful run.
- Link release pinning to new versioning page.
- Keep optional extras, but move contributor-only extras (`dev`, `validation`, `outcomes`) into a collapsed note or contributor docs.

### `docs/getting-started/sec-edgar-setup.md`

- Add example for setting env vars in:
  - macOS/Linux shell
  - Windows PowerShell
  - `.env` or process manager, if supported by app deployment docs
- Link to production notes.

### `docs/getting-started/quickstart-cli.md`

- Add expected success output for the first command.
- Add a local fixture-based command if there is a committed fixture intended for users.
- Keep ticker examples, but make EDGAR dependency explicit in command captions.

### `docs/getting-started/quickstart-python.md`

- Use `with open(..., encoding="utf-8")` in sample code.
- Show `result.to_dict().keys()` or a short printed output so users know success shape.
- Add a note about object types vs dict output.

### `docs/getting-started/understanding-scores.md`

- Keep as canonical score interpretation.
- Add a small "higher/lower means" table at the top.
- Clarify that `specificity_quality_score` is directionally different if it appears in components.
- Link to versioning and evidence pages.

### `docs/guides/http/index.md`

- Keep conceptual endpoint map.
- Link to generated endpoint reference.
- Move Postman collection file list to Examples Gallery or Reference.
- Keep only one unsupported-view explanation.
- Add a security/deployment callout: local API has no built-in public auth layer.

### `docs/reference/http/openapi.md`

- Add a command or script to export OpenAPI JSON.
- Link to generated endpoint reference.
- Avoid manually maintained schema summaries if generated docs exist.

### `docs/reference/python/index.md`

- Add a "Most users start with these helpers" section:
  - `score_filing_html`
  - `score_filing_ticker`
  - `extract_sections_from_html`
- Keep autodoc pages, but add short descriptions before module lists.

### `docs/methodology/index.md`

- Keep current separation of overview, research, and specs.
- Add a "Read this order" note:
  1. Overview
  2. Understanding Scores
  3. Evidence and Limitations
  4. Detailed specs

### `docs/methodology/research-foundation.md`

- Add linkcheck handling for DOI links that block automated clients.
- Keep licensing note.
- Avoid wording that implies built-in lists are exact LM lists.

### `docs/validation/evidence-and-limitations.md`

- Make this the canonical validation source.
- Reconcile counts:
  - exact corpus count
  - exact validation count
  - exact volatility cohort count
- Link to report files with commit-stable paths.
- Add "last validated on" date and package/artifact versions.

### `docs/appendix/changelog.md`

- Keep version history.
- Remove or shorten validation detail if canonical validation page has exact details.
- Link to evidence page for validation results.

### `docs/legal.md`

- Keep concise.
- Add linkcheck ignores or alternate SEC URLs if automated linkcheck remains noisy.
- Link to production notes for EDGAR and redistribution cautions.

### `docs/conf.py`

- Remove hidden public developer/contributor pages from build.
- Add `linkcheck_ignore` for bot-blocked external links, or set linkcheck retry/timeout policy.
- Consider adding `html_logo` or favicon if brand assets are available.
- Keep `exclude_patterns` explicit and add comments explaining why draft directories are excluded.

## Priority Roadmap

### P0: Public Hygiene

Goal: prevent embarrassing public pages and noisy checks.

Tasks:

- Remove hidden contributor/developer pages from public build.
- Delete or quarantine TODO stubs.
- Reconcile validation counts.
- Add linkcheck ignores for known bot-blocked DOI/SEC links.
- Run `sphinx-build -E -W -b html`.

### P1: First-Run Experience

Goal: make a new public user successful in under five minutes.

Tasks:

- Add First Successful Run page.
- Update installation, CLI quickstart, Python quickstart, and FAQ links.
- Add expected outputs and failure fixes.
- Add Examples Gallery.

### P2: Integration Reference

Goal: make HTTP/Python integrators confident.

Tasks:

- Generate endpoint reference from OpenAPI.
- Improve Python reference landing page.
- Add production/deployment notes.
- Link Postman collections from examples/reference.

### P3: Trust and Methodology

Goal: make claims auditable without overwhelming users.

Tasks:

- Add or promote canonical scope/claims page.
- Add versioning/reproducibility page.
- Trim duplicated disclaimers.
- Make methodology specs more scannable.

## Definition of Done

The public Read the Docs site is ready when:

- Fresh HTML build passes with warnings as errors.
- Linkcheck is either clean or has documented ignores for known bot-blocked sources.
- Public pages contain no `TODO`, `TBD`, or placeholder content.
- Contributor-only content is not built into public RTD pages.
- A first-time user can install, configure EDGAR, score a filing, and interpret the main fields from one guided path.
- Validation claims use one canonical count/source and do not drift across README, docs, changelog, and contributor guidance.
- HTTP and Python integrators can find endpoint/helper references without reading source code.
- Limitations are clear, but not repeated so often that they obscure supported workflows.
