# Boilerplate v4 diagnostics

Phase 0 baseline for `text_metrics_v4` cross-firm boilerplate blend.

## Blend weights (committed default)

| Weight | Value | Role |
|--------|------:|------|
| `w_p` (phrase) | **0.4** | `boilerplate_phrase_ratio` (sentence-normalized phrase hits) |
| `w_x` (cross-firm) | **0.6** | `boilerplate_cross_firm_ratio` (word-normalized LS-style 4-grams) |

Defined in `disclosure_alpha.boilerplate.DEFAULT_BLEND_WEIGHTS`.

## Mini-corpus smoke (n=3, public fixture)

Command:

```bash
python scripts/diagnose_boilerplate_blend.py \
  --corpus tests/fixtures/validation/mini_corpus.jsonl \
  --fiscal-year 2025
```

Observed on 2026-06-25 (committed FY2025 baseline built from same fixture):

| Metric pair | Spearman ρ |
|-------------|------------|
| `boilerplate_phrase_ratio` vs LS 4-gram | -0.50 |
| `boilerplate_combined_ratio` (0.4/0.6) vs LS | **1.00** |

The mini fixture is too small for production evidence claims. It confirms the combined metric tracks the LS reference when cross-firm grams are loaded.

## Full S&P 500 FY2025 cohort (internal branch)

Re-run completed on `internal` against `data/validation/corpus/sp500_item1a_fy2025.jsonl` (n=478):

1. `python scripts/build_boilerplate_baseline.py --corpus … --fiscal-year 2025`
2. `python scripts/diagnose_boilerplate_blend.py --corpus … --fiscal-year 2025`
3. L2 construct validation (`boilerplate_vs_ls4gram` uses `boilerplate_combined_ratio`)

**Observed:** Spearman ρ ≈ **0.96** vs LS 4-gram proxy on `boilerplate_combined_ratio` (target ≥ 0.80; phrase-only v3 was ≈0.74).

`docs/getting-started/evidence.md` headline boilerplate row is now updated to the completed v4 result.

## Discordant tickers

Export from L2 report `discordant_tickers.boilerplate_vs_ls4gram` after full corpus run. Use for phrase-list tuning only when cross-firm ratio and LS reference disagree materially.
