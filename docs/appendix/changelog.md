# Changelog

Version history for parser, metrics engine, dictionary packs, and scoring model.

## built_in_dictionaries_v2 / text_metrics_v2 (2026-06-21)

Shipped the built-in dictionary enrichment documented in {doc}`../methodology/metrics-engine`.

### Dictionary additions

| Pack | Count (approx.) | Notes |
|------|----------------:|-------|
| `NEGATIVE_WORDS` | 42 | Fraud, insolvency, impairment, outage terms |
| `UNCERTAINTY_WORDS` | 30 | Contingency, fluctuation, exposure terms |
| `LITIGIOUS_WORDS` | 26 | Arbitration, antitrust, indemnification terms |
| `CONSTRAINING_WORDS` | 28 | Covenant, lien, forbearance terms |
| Modal tiers | 18 | `WEAK_MODAL_WORDS`, `MODERATE_MODAL_WORDS`, `STRONG_MODAL_WORDS` |
| `BOILERPLATE_PHRASES` | 20 | Safe-harbor and generic risk language |
| `TOPIC_KEYWORDS` | 21 topics | Investable risk clusters for diff engine |
| `FLAG_PATTERNS` | 13 flags | SEC/PCAOB/FASB-grounded event phrases |
| `MDNA_DENSITY_TERMS` | 4 packs | MD&A uncertainty, demand, margin, liquidity density |

v2 flag phrase additions: `material weaknesses in internal control over financial reporting`, `plans are intended to mitigate`, `no longer expects`, `incident response`, `systems outage`.

`TERM_PACK_METADATA` now documents all shipped packs (negative, uncertainty, litigious, constraining, modal, boilerplate, topics, severity, flags, mdna_density, geography, segment).

### Matching behavior (metrics engine)

- **Boilerplate:** each phrase counted at most once per sentence.
- **Topics:** word-boundary phrase matching (no substring false positives); removed standalone `competitive` from competition topic.
- **Severity:** topic intensity uses severity words within ±10 tokens of a topic hit only.
- Shared helpers live in `disclosure_alpha.text_matching`.

### Version bumps

| Artifact | v1 | v2 |
|----------|----|----|
| `DICTIONARY_VERSION` | `built_in_dictionaries_v1` | `built_in_dictionaries_v2` |
| `METRICS_ENGINE_VERSION` | `text_metrics_v1` | `text_metrics_v2` |
| `SCORING_MODEL_VERSION` | unchanged | `deterministic_scoring_v1` |

### Validation (S&P 500 FY2025 Item 1A, n=428)

| Gate | Result |
|------|--------|
| Unit + snippet matrix | 227 tests passed (`tests/test_dictionary_snippets.py`, 50 curated near-miss fixtures) |
| Distribution shift vs baseline | `large_score_shift_frac=0.0` (gate ≤ 5%) |
| `boilerplate_vs_ls4gram` | Spearman ρ ≈ 0.69 (threshold ≥ 0.50) |
| `specificity_vs_ner` | Spearman ρ ≈ 0.84 (threshold ≥ 0.60) |

Baseline snapshot: `data/validation/baselines/dictionary_shift_baseline.json`.  
Shift report: `data/validation/reports/dictionary_shift_report.json`.

### Out of scope (deferred)

- External Loughran–McDonald loader
- Package split of `dictionaries.py`
- Flag suppressions (`no material weakness`) pending false-positive review

## built_in_dictionaries_v1 / text_metrics_v1

Initial license-safe built-in lists and deterministic text metrics engine.
