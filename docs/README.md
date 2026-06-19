# Deterministic Scoring Methodology

Production documentation for Disclosure Alpha's **deterministic-only** scoring layer: text metrics, section diffs, flags, and filing-level component aggregation — without LLM input.

## Audience

- Engineers implementing or extending `app/core/text_metrics.py`, `diff_engine.py`, `deterministic_scoring.py`
- Product/API owners defining free-tier vs composite-tier claims
- Validation owners running calibration and audit gates

## Version

| Artifact | Current | Next |
|----------|---------|------|
| `metrics_engine_version` | `text_metrics_v1.3` | `text_metrics_v2.0` (LM dictionary) |
| Scoring model | `deterministic_scoring_v3` | strict missing-metric semantics; outcome-calibrated weights (P3) |
| Dictionary | MVP built-in lists in `dictionaries.py` | LM-aligned + licensed expansion path |

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
# Run automated validation
python3.11 -m pytest -q

# Score a filing through the package CLI
disclosure-alpha score --html filing.html --form 10-K
```
