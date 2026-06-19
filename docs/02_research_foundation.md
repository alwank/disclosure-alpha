# 02 — Research Foundation

Maps peer-reviewed literature to Disclosure Alpha deterministic metrics. Use this doc to justify methodology to customers, auditors, and calibration users.

## Core references (read first)

| Paper | Citation | Validates |
|-------|----------|-----------|
| Loughran & McDonald (2011) | *J. Finance* 66(1), 35–65. [DOI](https://doi.org/10.1111/j.1540-6261.2010.01625.x) | Finance-specific word lists; links tone to returns, volatility, fraud, **material weakness** |
| Loughran & McDonald (2016) | *J. Accounting Research* 54(4), 1187–1230. [DOI](https://doi.org/10.1111/1475-679X.12123) | Implementation pitfalls; validation playbook for textual measures |
| Cohen, Malloy & Nguyen (2020) | *J. Finance* 75(3), 1371–1415. [DOI](https://doi.org/10.1111/jofi.12885) | **Filing text changes** predict returns, earnings, bankruptcy; cosine similarity |
| Hope, Hu & Lu (2016) | *Rev. Accounting Studies* 21(4), 1005–1045. [DOI](https://doi.org/10.1007/s11142-016-9371-1) | **Specificity** of risk-factor text → market reaction |
| Lang & Stice-Lawrence (2015) | *J. Accounting & Economics* 60(2–3), 421–451. [DOI](https://doi.org/10.1016/j.jacceco.2015.09.003) | **Boilerplate** → lower liquidity, institutional ownership |
| Dyer, Lang & Stice-Lawrence (2017) | *JAE* 64(2), 221–245. [DOI](https://doi.org/10.1016/j.jacceco.2017.07.002) | Topic trends; stickiness; risk-factor / IC sections drive boilerplate |

## Metric family → literature map

### Word-list tone ratios

| Our metric | LM category | Key finding |
|------------|-------------|-------------|
| `negative_word_ratio` | Negative | Predicts filing-date returns, volatility; elevated in fraud samples |
| `uncertainty_word_ratio` | Uncertainty | Predicts volatility; IPO uncertainty → offer revisions |
| `litigious_word_ratio` | Litigious | Elevated in litigation / regulatory contexts |
| `modal_word_ratio` | Modal (weak/strong) | Weak commitment language in MD&A |
| `constraining_word_ratio` | (custom; related to LM constraining) | Covenant / obligation language → liquidity stress |

**Implementation note:** We use a **minimal MVP dictionary** (`app/core/dictionaries.py`). Literature uses the full [Loughran–McDonald lists](https://www.nd.edu/~mcdonald/Word_Lists.html). v2 upgrade: align tokenization and lists with LM for replication studies.

### Specificity

| Our metric | Literature measure | Gap |
|------------|-------------------|-----|
| `numeric_specificity_score` | Hope et al. numeric entities / 1000 words | We count numeric tokens; they use NER + scaled counts |
| `company_specificity_score` | Hope et al. NER entities (orgs, places, %) | We proxy via capitals, geo, segment terms |

**Validation target:** Spearman ρ > 0.6 vs Hope-style NER specificity on Item 1A sample (n ≥ 200).

### Boilerplate

| Our metric | Literature measure | Gap |
|------------|-------------------|-----|
| `boilerplate_phrase_ratio` | Lang & Stice-Lawrence: % words in shared 4-gram phrases across firms | We use fixed phrase list, not cross-firm phrase frequency |

**Validation target:** Positive correlation between our ratio and LS-L boilerplate on same fiscal year.

### Readability

| Our metric | Literature | Gap |
|------------|------------|-----|
| `readability_score` | Li (2008) Fog index; Miller (2010) | Custom heuristic (sentence length + long words). LM survey warns Fog misclassifies financial terms |

**v2 target:** Report Fog alongside custom score; do not claim Li (2008) replication.

### Section change

| Our metric | Literature | Alignment |
|------------|------------|-----------|
| `lexical_similarity` | Cohen et al. cosine similarity | Direct |
| `semantic_similarity` | Cohen et al. + embedding literature | Extension beyond their baseline |
| `disclosure_change_score` | Cohen et al. "changer" signal | Our formula is a weighted composite, not their exact portfolio sort |
| `new_topics` / `intensified_topics` | Dyer et al. LDA topics | Simpler keyword-cluster proxy |
| `language_deltas` | LM tone change; Hahn et al. (2018) uncertainty | `(current_ratio - prior_ratio) × 100` |

### Boolean flags

| Our flag | Literature support |
|----------|-------------------|
| `material_weakness_flag` | LM (2011) ICW sample; Doyle, Ge & McVay (2007) |
| `restatement_flag` | LM fraud/restatement samples |
| `going_concern_flag` | Mayew, Sethuraman & Venkatachalam (2015) MD&A tone → GCO |
| `investigation_flag` | Cohen et al. — litigation language changes informative |
| `guidance_withdrawal_flag` | Practitioner + event-study literature (no single canonical paper) |

**Validation target:** Precision/recall vs external event databases for ICW and restatements.

## Outcome variables for calibration

When validating deterministic scores empirically, use outcomes from the literature:

| Outcome | Papers | Horizon |
|---------|--------|---------|
| Realized volatility | LM 2011, Kravet & Muslu 2013 | 30–90 days post-filing |
| Earnings surprise | LM 2011, Cohen et al. 2020 | Next quarter |
| Return spread (change quintile) | Cohen et al. 2020 | 3–12 months |
| Material weakness disclosure | LM 2011 | Concurrent |
| Going-concern opinion | Mayew et al. 2015 | Same fiscal year |
| Analyst forecast dispersion | Hope et al. 2016 | Post-filing |

We do **not** require statistically significant return prediction for MVP launch. We require **directional monotonicity** on at least two outcome families before claiming "validated" in API docs.

## Secondary references

| Paper | Use |
|-------|-----|
| Li (2008), *JAE* — readability & earnings persistence | Readability context; use with caveats |
| Kravet & Muslu (2013) — textual risk disclosures | Risk-factor quantity/tone → volatility |
| Huang, Teoh & Zhang (2014) — abnormal tone | Future v2: abnormal tone = tone − expected tone |
| Campbell et al. (2014) — mandatory risk factors | Item 1A focus |
| Hahn, Littig & Pinkwart (2018), ACL — uncertainty embeddings | Uncertainty delta validation |
| Bochkay et al. (2023), *CAR* — textual analysis survey | Topic modeling next steps |

## Licensing note

Loughran–McDonald word lists are **free for academic use**; commercial use requires permission from the authors. Our MVP built-in lists avoid licensing risk. **v2:** obtain commercial license or ship LM-aligned lists under explicit license terms before marketing "Loughran–McDonald-based" scoring.
