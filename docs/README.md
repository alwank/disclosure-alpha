# Deterministic Scoring Methodology

Production documentation for Disclosure Alpha's **deterministic-only** scoring layer: text metrics, section diffs, flags, and filing-level component aggregation — without LLM input.

## Audience

- Engineers implementing or extending `app/core/text_metrics.py`, `diff_engine.py`, `deterministic_scoring.py`
- Product/API owners defining deterministic-only product claims
- Validation owners running calibration and audit gates

## Version

| Artifact | Current | Next |
|----------|---------|------|
| `metrics_engine_version` | `text_metrics_v1.3` | `text_metrics_v2.0` (LM dictionary) |
| Scoring model | `deterministic_scoring_v3` | strict missing-metric semantics; outcome-calibrated weights (P3) |
| Dictionary | MVP built-in lists in `dictionaries.py` | LM-aligned + licensed expansion path |

**Validation status (FY2025):** L0 + L1 pass. **Partial L2:** construct on ~425-firm cohort. **Partial L3 (vol only, closed for MVP):** Q5/Q1 ~ 1.11, n ~ 435 (FY2025 corpus). Earnings gate failed on FY2024 robustness run — do not claim. See [07_validation_protocol.md](./07_validation_protocol.md).

## Document map

| Doc | Purpose |
|-----|---------|
| [01_overview.md](./01_overview.md) | Scope, pipeline stages, product claims, score interpretation |
| [02_research_foundation.md](./02_research_foundation.md) | Academic papers mapped to each metric family |
| [03_metrics_spec.md](./03_metrics_spec.md) | Text metrics, flags, MD&A densities — current + v2 target |
| [04_diff_spec.md](./04_diff_spec.md) | Section diff engine, change score, language deltas |
| [05_aggregation_spec.md](./05_aggregation_spec.md) | 10 component formulas, weights, coverage, confidence |
| [06_v2_improvement_plan.md](./06_v2_improvement_plan.md) | Prioritized upgrades from literature → code |
| [07_validation_protocol.md](./07_validation_protocol.md) | Empirical validation tests, gates, acceptance criteria |
| [08_dictionary_enrichment_research.md](./08_dictionary_enrichment_research.md) | Category-by-category dictionary enrichment research and implementation rules |
| [09_product_surfaces.md](./09_product_surfaces.md) | Product map: HTTP endpoints, MCP bundles, response tiers |

## Code map

```
app/core/dictionaries.py      → word lists, flags, topic keywords, MD&A density terms
app/core/text_metrics.py      → per-section feature extraction
app/core/diff_engine.py       → prior-section comparison
app/core/deterministic_scoring.py → filing-level component aggregation
app/services/metrics_service.py   → persist + orchestrate deterministic stage
```

## Quick start

```bash
# L0 + L1 (pytest) and L2 harness unit tests
python3.11 -m pytest -q

# Audit S&P 500 corpus quality (no network)
python scripts/audit_validation_corpus.py

# Full L2 validation on S&P 500 corpus (slow; requires spaCy)
export SEC_USER_AGENT="YourName your@email.com"
PYTHONUNBUFFERED=1 .venv/bin/python scripts/validate_deterministic_construct.py \
  --universe data/universe/sp500.csv

# Score a filing through the package CLI
disclosure-alpha score --html filing.html --form 10-K
```

L2 corpus format and env vars: [data/validation/README.md](../data/validation/README.md).
