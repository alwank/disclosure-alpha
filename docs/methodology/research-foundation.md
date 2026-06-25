# Research Foundation

Peer-reviewed finance and accounting literature motivates the deterministic metrics in Disclosure Alpha. This page maps papers to what the open-source engine measures today.

Empirical results on the current release: {doc}`../getting-started/evidence`.

## Core references

| Paper | Citation | Relevance |
|-------|----------|-----------|
| Loughran & McDonald (2011) | *J. Finance* 66(1), 35–65. [DOI](https://doi.org/10.1111/j.1540-6261.2010.01625.x) | Finance-specific word lists; tone links to returns, volatility, fraud, material weakness |
| Loughran & McDonald (2016) | *J. Accounting Research* 54(4), 1187–1230. [DOI](https://doi.org/10.1111/1475-679X.12123) | Implementation pitfalls for textual measures |
| Cohen, Malloy & Nguyen (2020) | *J. Finance* 75(3), 1371–1415. [DOI](https://doi.org/10.1111/jofi.12885) | Filing text changes predict returns, earnings, bankruptcy |
| Hope, Hu & Lu (2016) | *Rev. Accounting Studies* 21(4), 1005–1045. [DOI](https://doi.org/10.1007/s11142-016-9371-1) | Specific risk-factor disclosure → market reaction |
| Lang & Stice-Lawrence (2015) | *J. Accounting & Economics* 60(2–3), 421–451. [DOI](https://doi.org/10.1016/j.jacceco.2015.09.003) | Boilerplate risk-factor language → liquidity effects |
| Dyer, Lang & Stice-Lawrence (2017) | *JAE* 64(2), 221–245. [DOI](https://doi.org/10.1016/j.jacceco.2017.07.002) | Topic trends and stickiness in 10-K text |

## Word-list tone ratios

| Our metric | Literature category | Finding |
|------------|---------------------|---------|
| `negative_word_ratio` | LM Negative | Associated with filing-date returns, volatility, fraud samples |
| `uncertainty_word_ratio` | LM Uncertainty | Associated with volatility |
| `litigious_word_ratio` | LM Litigious | Elevated in litigation / regulatory contexts |
| `modal_word_ratio` | LM Modal | Weak commitment language in MD&A |
| `constraining_word_ratio` | Custom (LM-adjacent) | Covenant / obligation language → liquidity stress proxy |

**Implementation:** Built-in word lists in `src/disclosure_alpha/dictionaries/` (`built_in_dictionaries_v3`). These are finance-inspired curated lists shipped with the repo — not a redistribution of the full [Loughran–McDonald master dictionary](https://sraf.nd.edu/loughranmcdonald-master-dictionary/).

## Specificity

| Our metric | Literature basis |
|------------|------------------|
| `numeric_specificity_score` | Hope et al. — numeric detail in risk factors; we count numeric tokens per 100 words |
| `company_specificity_score` | Hope et al. — entity specificity; we proxy via capitalized terms, geography, and segment phrases |

## Boilerplate

| Our metric | Literature basis |
|------------|------------------|
| `boilerplate_phrase_ratio` | Lang & Stice-Lawrence — boilerplate risk-factor language; fixed phrase list matched per section |
| `boilerplate_cross_firm_ratio` | Lang & Stice-Lawrence — cross-firm 4-gram word share (`text_metrics_v4`) |
| `boilerplate_combined_ratio` | Blended production boilerplate input for `boilerplate_risk_score` (`text_metrics_v4`) |

Our phrase measure is a section-level phrase hit rate. The cross-firm measure uses committed universe 4-gram frequency — closer to the LS validation reference than phrase-only v3.

## Readability

| Our metric | Literature basis |
|------------|------------------|
| `readability_score` | Inspired by readability literature (Li 2008; Miller 2010); implemented as a custom heuristic from sentence length and long-word share |

Used inside the MD&A uncertainty blend — not a standalone Fog index replication.

## Section change

| Our metric | Literature basis |
|------------|------------------|
| `lexical_similarity` | Cohen et al. — TF-IDF cosine similarity |
| `semantic_similarity` | Embedding-based similarity (extension beyond Cohen et al. baseline) |
| `disclosure_change_score` | Cohen et al. "changer" concept — weighted composite of similarity, length, and topic shifts |
| `new_topics` / `intensified_topics` | Dyer et al. topic framing — keyword-cluster proxy |
| `language_deltas` | Tone change vs prior section: `(current_ratio − prior_ratio) × 100` |

Details: {doc}`diff-engine`.

## Boolean flags

Hard-event phrase flags (material weakness, restatement, going concern, etc.) are grounded in SEC disclosure language and supported by LM (2011) and related event-literature. Flags fire only in scoped sections — see {doc}`metrics-engine`.

## Licensing note

Loughran–McDonald word lists are free for academic use; commercial redistribution requires separate permission. Disclosure Alpha ships its own built-in lists to avoid licensing ambiguity. Do not describe scores as "Loughran–McDonald-based" unless you load licensed LM lists yourself.

## Related

- {doc}`overview`
- {doc}`../getting-started/evidence`
- {doc}`../getting-started/scope-and-claims`
