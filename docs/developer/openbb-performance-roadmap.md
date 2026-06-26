# OpenBB performance roadmap

> **Status (2026):** OpenBB ships a single **`disclosure_company`** widget and `/openbb/company` endpoint. Legacy score-card, screener, flags, and section-changes widgets were removed. Multi-ticker screening remains on the REST API (`POST /v1/panel/disclosure-matrix`).

Performance work for **Disclosure Alpha** in OpenBB Workspace and the shared API pipeline. OpenBB-specific items **PR-A, PR-B, and PR-D** are **implemented**. **PR-C** was superseded by the bundled widget. **PR-E** applies to the REST panel path only (not OpenBB).

**Context:** Each **Run** on the Company widget calls `metrics_filing_ticker(..., compare_prior=True)` once — score card, flags, and section changes in one HTML response. That path resolves filings, downloads HTML (disk cache helps), parses with sec-parser, computes section metrics, and runs diffs vs the prior filing.

**Out of scope:** distributed cache (Redis), pre-warming jobs, async EDGAR client rewrite, or changing scoring semantics.

---

## Implementation status

| PR | Scope | Status |
|----|-------|--------|
| **PR-A** | In-process TTL cache on `metrics_filing_ticker` | **Done** — `cache.py`, `METRICS_CACHE_*` |
| **PR-B** | API default `EMBEDDING_BACKEND=tfidf` | **Done** — `app_factory.py` |
| **PR-C** | `compare_prior=false` for active-flags endpoint | **Superseded** — flags endpoint removed; bundle needs prior for section changes |
| **PR-D** | Company tab bundle (one Run) | **Done** — `disclosure_company` widget |
| **PR-E** | Panel screener parallelism + cache reuse | **Done** — `score_panel_tickers` (REST API only) |
| **EDGAR-1/2** | Metadata-first filing resolution | **Done** — `resolve_filing_with_prior()` |

---

## PR-A — In-process TTL cache for filing metrics *(implemented)*

### Problem

Repeated requests for the same `(ticker, fiscal_year, form_type, quarter, compare_prior)` re-parse and re-score from scratch within the same API process. Re-Run on the Company widget amplifies this.

### Solution

1. `src/disclosure_alpha/cache.py` — thread-safe TTL dict:
   - Key: `(ticker.upper(), fiscal_year, form_type, quarter or None, compare_prior)`.
   - TTL: **`METRICS_CACHE_TTL_SECONDS`** (default **300**; `0` disables).
   - Max entries: **`METRICS_CACHE_MAX_SIZE`** (default **64**); FIFO eviction on overflow (ponytail: upgrade to LRU if needed).

2. Wraps **`metrics_filing_ticker`** only.

3. Cache is **per process** — multi-worker deployments (gunicorn `-w 4`) get one cache per worker.

4. Does not cache probe/demo paths or error results.

### Tests

`tests/test_metrics_cache.py` — hit/miss/TTL/disable, separate keys for `compare_prior`.

---

## PR-B — Default `EMBEDDING_BACKEND=tfidf` for API *(implemented)*

### Problem

Without `EMBEDDING_BACKEND=tfidf`, the first live run loads **sentence-transformers** (`all-MiniLM-L6-v2`) for `semantic_similarity` in section diffs — often 10–30+ seconds and hundreds of MB RAM.

### Solution

`disclosure-alpha-api` sets `EMBEDDING_BACKEND=tfidf` via `os.environ.setdefault` in `app_factory.py` unless the operator opts in:

- **tfidf:** fast, no extra install, slightly different change scores.
- **semantic:** install `[semantic]`, set `EMBEDDING_BACKEND=semantic` for MiniLM.

CLI/SDK callers are unchanged — only the API entrypoint sets the default.

---

## PR-C — `compare_prior=false` for active flags *(superseded)*

Originally planned for `/openbb/active-flags`, which called `metrics_filing_ticker(..., compare_prior=True)` even though flags use current-section metrics only.

**Superseded:** the active-flags endpoint and separate flags widget were removed in favor of the bundled **`disclosure_company`** widget (PR-D). That bundle includes section changes, which require the prior filing — so `compare_prior=True` is correct for the only OpenBB live path. No separate `compare_prior=False` cache slot is needed.

---

## PR-D — Company tab bundle (one Run) *(implemented)*

### Problem (historical)

Company tab had **three widgets** (score card, flags, changes). OpenBB issued **three HTTP requests** per Run.

### Solution

Single **`disclosure_company`** HTML widget:

- `GET /openbb/company` → score card + flags + section changes in one `HTMLResponse`.
- `widgets.json` / `apps.json` — one widget on the Company tab.
- One `metrics_filing_ticker(..., compare_prior=True)` + `score_for_model` per Run.
- Probe/validation (`_is_probe`, no query string) returns demo combined HTML.

Legacy `/openbb/disclosure-score-card`, `/openbb/active-flags`, `/openbb/section-changes`, and `/openbb/panel-screener` return **404**.

### Tests

`tests/test_openbb.py` — single pipeline call, HTML markers for flags and section changes.

---

## PR-E — Panel screener parallelism + cache reuse *(implemented, REST API only)*

Originally motivated by an OpenBB **Screen** tab. That tab was removed; batch screening is **`POST /v1/panel/disclosure-matrix`** only.

### Solution

1. `score_panel_tickers` uses **`metrics_filing_ticker`** (PR-A cache) + **`score_for_model`** instead of `score_filing_ticker`.

2. **`score_panel_tickers(..., max_workers=4)`** via `ThreadPoolExecutor` — worker count from **`PANEL_MAX_WORKERS`** (default **4**). SEC client throttle (~9 req/s) serializes network across workers in-process.

3. Per-ticker error isolation and `PanelBatchResult` shape preserved.

### Tests

`tests/test_panel_parallel.py` — order preservation, error isolation, cache reuse.

---

## EDGAR-1 + EDGAR-2 *(implemented)*

Filing resolution for `compare_prior=True` uses **one submissions fetch** and **metadata-first** accession selection:

| Change | Effect |
|--------|--------|
| `resolve_filing_with_prior()` | Current + prior year resolved in one scan |
| Metadata-first scoring | No exploratory full HTML downloads during submission scan |
| Bounded disambiguation | At most 3 `fetch_text_prefix` calls per target when metadata ties |
| `load_filing_bundle` | Two full HTML downloads max (current + prior) via `load_filing_html` |

**Expected cold `edgar` timing:** roughly half of pre-EDGAR-1 baseline (e.g. ~19s → ~8–12s for AAPL FY2025, network-dependent). Warm disk cache remains sub-second for HTML reads.

---

## Verification checklist

| Scenario | Expected |
|----------|----------|
| Company tab, AAPL FY2025, first Run | One EDGAR current+prior fetch, one parse; no sentence-transformers load (API default) |
| Company tab, second Run within 5 min | Sub-second; metrics cache hit |
| Panel POST, 10 tickers | Concurrent fetches; wall clock &lt; 10× single-ticker sequential |
| `demo=1` or probe (no query) | Fixture HTML; no cache pollution |
| Legacy OpenBB routes | 404 |

---

## Related

- {doc}`../guides/openbb/index` — user guide (connect and run)
- {doc}`../guides/production` — multi-worker deployment (cache per worker)
- {doc}`../reference/environment-variables` — env reference
