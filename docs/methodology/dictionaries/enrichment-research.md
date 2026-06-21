# 08 - Dictionary Enrichment Research and Implementation Guide

This document defines how to enrich `src/disclosure_alpha/dictionaries.py` without turning
the deterministic model into an uncalibrated keyword dump. It covers each current word and
phrase category, the research basis, candidate expansion direction, matching rules, tests,
and versioning requirements.

## Executive Summary

The current dictionary is intentionally small and license-safe. Enrichment should proceed in
three layers:

1. **Built-in safe lists**: small, hand-curated finance terms shipped in this repo.
2. **Phrase/event packs**: SEC/PCAOB/FASB-grounded phrase rules for hard events such as
   material weaknesses, going concern, cybersecurity incidents, covenant breaches, and
   legal proceedings.
3. **Optional external licensed lists**: full Loughran-McDonald-style dictionaries loaded
   from an external file or package when license terms permit.

Do not paste the full Loughran-McDonald lists into this repo unless the license review allows
redistribution. Use the official source as the canonical reference and keep a loader path for
licensed deployments.

## Research Sources

Primary and high-relevance sources used for this guide:

- Loughran-McDonald Master Dictionary: https://sraf.nd.edu/loughranmcdonald-master-dictionary/
- Loughran and McDonald, "When Is a Liability Not a Liability? Textual Analysis, Dictionaries, and 10-Ks", Journal of Finance, 2011: https://doi.org/10.1111/j.1540-6261.2010.01625.x
- Cohen, Malloy, and Nguyen, "Lazy Prices", Journal of Finance, 2020: https://doi.org/10.1111/jofi.12885
- Hope, Hu, and Lu, "The Benefits of Specific Risk-Factor Disclosures", Review of Accounting Studies, 2016: https://doi.org/10.1007/s11142-016-9371-1
- Lang and Stice-Lawrence, "Textual Analysis and International Financial Reporting", Journal of Accounting and Economics, 2015: https://doi.org/10.1016/j.jacceco.2015.09.002
- Dyer, Lang, and Stice-Lawrence, "The Evolution of 10-K Textual Disclosure", Journal of Accounting and Economics, 2017: https://doi.org/10.1016/j.jacceco.2017.07.002
- SEC Regulation S-K Item 105 risk factors: https://www.ecfr.gov/current/title-17/chapter-II/part-229/subpart-229.100/section-229.105
- SEC 2020 Regulation S-K modernization final rule: https://www.sec.gov/files/rules/final/2020/33-10825.pdf
- SEC MD&A guidance: https://www.sec.gov/rules-regulations/2003/12/commission-guidance-regarding-managements-discussion-analysis-financial-condition-results-operations
- SEC Form 8-K: https://www.sec.gov/files/form8-k.pdf
- SEC cybersecurity incident disclosure guide: https://www.sec.gov/resources-small-businesses/small-business-compliance-guides/cybersecurity-risk-management-strategy-governance-incident-disclosure
- PCAOB AS 2201 internal control audit standard: https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201
- PCAOB AS 1305 control deficiencies: https://pcaobus.org/oversight/standards/auditing-standards/details/AS1305
- PCAOB AS 2415 going concern: https://pcaobus.org/oversight/standards/auditing-standards/details/AS2415
- FASB ASU 2014-15 going concern: https://storage.fasb.org/ASU%202014-15.pdf

## Global Implementation Rules

### Dictionary Structure

Keep the current constants for backward compatibility, but introduce metadata before adding
large expansions:

```python
DICTIONARY_VERSION = "built_in_dictionaries_v2"

TERM_PACK_METADATA = {
    "negative": {
        "source": "built_in_finance_curated",
        "match_type": "token",
        "consumer": ["negative_word_ratio", "risk_factor_intensity_score"],
        "license": "repo_safe_manual_curation",
    },
}
```

The metadata does not need to drive runtime behavior immediately, but it gives users and
API consumers a stable audit trail.

### Matching Rules

- **Token lists**: lowercase exact token match only; use word boundaries.
- **Phrase lists**: lowercase phrase match with word boundaries around the phrase; allow
  internal whitespace and hyphen variants where common.
- **Regex patterns**: only for flags where proximity or grammar matters.
- **No stemming by default**: add explicit inflections to avoid false positives.
- **No substring matching for single words**: `default` must not match `defaultedness`;
  `investigation` must not match `reinvestigation`.
- **Context windows for event flags**: hard flags should use phrase or regex evidence within
  a narrow section scope, not broad words alone.
- **Negation handling**: do not apply sentiment-level negation globally in v2. For event flags,
  add targeted suppressions such as `no material weakness` only after testing false negatives.

### Acceptance Criteria for Any New Term

Every new term or phrase must satisfy at least one of:

- It appears in a recognized finance/accounting dictionary category.
- It is directly grounded in SEC, PCAOB, FASB, or Form 8-K disclosure language.
- It appears repeatedly in SEC filing snippets for the intended section.
- It materially improves a validation metric without increasing false positives.

Every addition needs at least one fixture-level test:

- positive trigger,
- near-miss non-trigger,
- section-scope check where applicable,
- monotonic density or ratio check if the term feeds a score.

## Category Research and Enrichment Rules

### 1. `NEGATIVE_WORDS`

**Current purpose:** Drives `negative_word_ratio`, `risk_factor_intensity_score`, and
`tone_negativity_score`.

**Research basis:** Loughran-McDonald shows general-purpose negative lists misclassify many
financial words; finance-specific negative words should be selected for negative meaning in
filings, not ordinary English sentiment.

**Enrichment direction:**

- Keep as token-only.
- Prefer words tied to loss, impairment, disruption, deterioration, default, breach, failure,
  insolvency, fraud/restatement, and operational harm.
- Add explicit inflections rather than stemming.

**Candidate built-in additions to review:**

- `impaired`, `impair`, `impairments`
- `disruption`, `disruptions`, `disrupted`
- `bankruptcy`, `bankrupt`, `insolvency`, `insolvent`
- `delinquency`, `delinquencies`, `delinquent`
- `write-down`, `writedown`, `writeoff`, `write-off`
- `charge-off`, `chargeoffs`, `charge-offs`
- `recall`, `recalls`
- `outage`, `outages`
- `misstatement`, `misstatements`
- `fraud`, `fraudulent`

**Do not add without special handling:**

- `capital`, `liability`, `tax`, `foreign`, `risk`; these are common filing words and weak
  standalone negative signals.
- `claims`; it is better in litigious context because product/warranty claims can be neutral
  in some industries.

**Implementation rules:**

- Token match only.
- Add tests proving `risk factors` heading text does not inflate negative tone.
- Add industry smoke tests for banks, insurers, software, manufacturing, and biotech because
  negative vocabulary differs heavily by sector.

### 2. `UNCERTAINTY_WORDS`

**Current purpose:** Drives `uncertainty_word_ratio`, `risk_factor_intensity_score`,
`mdna_uncertainty_score`, and language deltas.

**Research basis:** Loughran-McDonald has an uncertainty category; SEC MD&A guidance also
emphasizes known trends, demands, commitments, events, and uncertainties.

**Enrichment direction:**

- Split simple modal uncertainty from event uncertainty in future versions.
- Keep token list conservative; phrase uncertainty belongs in MD&A density packs.

**Candidate built-in additions to review:**

- `approximate`, `approximately`
- `contingency`, `contingencies`, `contingent`
- `fluctuate`, `fluctuates`, `fluctuation`, `fluctuations`
- `variable`, `variability`
- `unresolved`, `pending`
- `exposure`, `exposures`, `exposed`
- `susceptible`
- `unforeseen`
- `undetermined`
- `assumption`, `assumptions`

**Do not add without context:**

- `estimate`, `estimated`, `estimates`; common accounting language can be normal disclosure.
- `believe`; better handled in weak modal language.

**Implementation rules:**

- Token match only.
- Add a fixture where injecting uncertainty terms raises ratio monotonically.
- Track `uncertainty_word_ratio` and `modal_word_ratio` separately; do not let uncertainty
  become a duplicate of weak modal language.

### 3. `LITIGIOUS_WORDS`

**Current purpose:** Drives `litigious_word_ratio`, `legal_regulatory_risk_score`, and legal
language deltas.

**Research basis:** Loughran-McDonald includes litigious terms; Cohen, Malloy, and Nguyen
find changes in litigation/lawsuit language especially informative in filing-change analysis.

**Enrichment direction:**

- Separate legal process words from regulatory enforcement phrases.
- Keep ambiguous words like `claim` but consider weighting them lower later.

**Candidate built-in additions to review:**

- `arbitration`, `arbitrations`
- `appeal`, `appeals`, `appellate`
- `antitrust`
- `allegation`, `allegations`, `alleged`
- `damages`
- `injunction`, `injunctive`
- `indemnification`, `indemnify`
- `sanction`, `sanctions`
- `decree`
- `consent`, only as phrase `consent decree` or `consent order`
- `cease-and-desist`, `cease and desist`

**Do not add as standalone tokens:**

- `order`, `matter`, `action`, `case`; too broad without legal context.
- `material`; use severity words or event proximity, not litigious ratio.

**Implementation rules:**

- Token list for legal nouns.
- Phrase list for regulatory enforcement events.
- Add a future `LEGAL_REGULATORY_PHRASES` pack with phrases such as `civil investigative demand`,
  `wells notice`, `consent order`, `cease and desist order`, `regulatory enforcement action`.
- Test near misses like ordinary customer `claims` and `order backlog`.

### 4. `CONSTRAINING_WORDS`

**Current purpose:** Drives `constraining_word_ratio`, `liquidity_stress_score`, and internal
controls risk when Item 1A contains constraint language.

**Research basis:** Loughran-McDonald includes constraining words; SEC MD&A rules focus on
known demands, commitments, liquidity, capital resources, and material cash requirements.

**Enrichment direction:**

- Use token terms for contract/debt constraints.
- Use phrase terms for covenant and liquidity events.

**Candidate built-in additions to review:**

- `restricted`, `restrictive`
- `waiver`, `waivers`
- `forbearance`
- `acceleration`, `accelerated`
- `maturity`, `maturities`
- `refinance`, `refinancing`
- `collateral`
- `lien`, `liens`
- `pledged`
- `encumbered`
- `obligated`

**Do not add without context:**

- `required`, `requirement`, `requirements`; too common in legal/accounting prose.
- `compliance`; current list includes it, but it is broad and should be monitored for false
  positives.

**Implementation rules:**

- Keep `default` in constraining but add tests for accounting/default-settings contexts.
- Add phrase density terms for liquidity-specific contexts instead of broadening token ratios.
- Use MD&A section scope for liquidity stress; use Item 1A as supplemental tone only.

### 5. `MODAL_WORDS`

**Current purpose:** Drives `modal_word_ratio` and `mdna_uncertainty_score`.

**Research basis:** Loughran-McDonald distinguishes strong and weak modal words. The current
single `MODAL_WORDS` list mixes weak uncertainty (`may`, `might`) with management-intent verbs
(`expect`, `intend`, `believe`).

**Enrichment direction:**

- Introduce `WEAK_MODAL_WORDS`, `MODERATE_MODAL_WORDS`, and `STRONG_MODAL_WORDS`.
- Keep `MODAL_WORDS = WEAK_MODAL_WORDS | MODERATE_MODAL_WORDS | STRONG_MODAL_WORDS` for
  backward compatibility.

**Candidate split:**

- Weak: `may`, `might`, `could`, `possibly`, `possible`
- Moderate: `should`, `would`, `expect`, `expects`, `believe`, `believes`, `intend`, `intends`
- Strong: `must`, `will`, `shall`, `required`, `obligated`

**Implementation rules:**

- Do not change scoring formula until split metrics are emitted.
- Add `weak_modal_word_ratio` and `strong_modal_word_ratio` in a future metric version.
- In MD&A uncertainty, weak modal should increase uncertainty; strong modal may indicate
  obligation or commitment and should not automatically increase uncertainty.

### 6. `BOILERPLATE_PHRASES`

**Current purpose:** Feeds `boilerplate_phrase_ratio` and `boilerplate_risk_score`.

**Research basis:** SEC Item 105 discourages generic risks that apply to any registrant and
requires risk factors to explain how each risk affects the registrant. Lang and Stice-Lawrence,
and Dyer, Lang, and Stice-Lawrence support measuring boilerplate, stickiness, redundancy, and
specificity rather than relying only on a fixed phrase list.

**Enrichment direction:**

- Keep phrase list small and focused on safe harbor/generic risk language.
- Do not treat all common disclosure phrases as bad; boilerplate is best measured by cross-firm
  n-gram frequency and year/industry context.

**Candidate built-in additions to review:**

- `we face risks and uncertainties`
- `risks and uncertainties described below`
- `could materially and adversely affect`
- `material adverse effect on our business`
- `no assurance can be given`
- `may not be successful`
- `may fail to`
- `subject to a number of risks`
- `unknown risks and uncertainties`
- `not exhaustive`

**Implementation rules:**

- Phrase match only.
- Count at most once per sentence per phrase to avoid repeated boilerplate exploding a ratio.
- Add future `boilerplate_cross_firm_ratio` based on shared 4-grams within fiscal year and
  peer universe; do not overfit the static phrase list.
- Test that company-specific sentences with numbers and named segments offset boilerplate in
  `boilerplate_risk_score`.

### 7. `GEOGRAPHY_TERMS` and `SEGMENT_TERMS`

**Current purpose:** Proxy company specificity in `company_specificity_score`.

**Research basis:** Hope, Hu, and Lu measure specificity in qualitative risk-factor disclosures;
their construct is closer to named entities, numbers, and concrete details than a fixed geography
word list.

**Enrichment direction:**

- Keep these as fallback specificity proxies.
- Prefer NER/entity density in a future feature flag.
- Add only terms that indicate concrete company exposure, not generic global language.

**Candidate geography additions to review:**

- Major region tokens: `north america`, `latin america`, `emea`, `european union`, `apac`
- Country names only if matching uses phrase/token normalization and does not over-count
  common company names.

**Candidate segment additions to review:**

- `brand`, `brands`
- `channel`, `channels`
- `market`, `markets`
- `platform`, `platforms`
- `subscription`, `subscriptions`
- `service line`, `service lines`
- `geography`, `geographies`

**Implementation rules:**

- Use phrase-aware matching for multi-word terms.
- Do not let generic terms such as `market` dominate; cap contribution per sentence or per
  term family.
- Future NER should supersede this category for `specificity_quality_score`.

### 8. `TOPIC_KEYWORDS`

**Current purpose:** Diff engine detects new, removed, and intensified topics in changed
sections.

**Research basis:** Cohen, Malloy, and Nguyen support filing-change analysis; Dyer, Lang, and
Stice-Lawrence use topic modeling to study evolving 10-K disclosure topics. The current keyword
clusters are an explainable proxy for topic modeling.

**Enrichment direction:**

- Keep topics coarse and investable/risk-relevant.
- Add topic packs only when they can be tested with realistic filing snippets.
- Prefer phrase evidence over single generic terms.

**Recommended topic taxonomy additions:**

- `ai/data/privacy`: `artificial intelligence`, `machine learning`, `privacy law`,
  `consumer data`, `data processing`, `model risk`
- `tax`: `tax audit`, `tax examination`, `uncertain tax position`, `transfer pricing`
- `credit/default`: `credit deterioration`, `delinquency`, `nonperforming`, `charge-off`
- `banking/capital`: `capital ratio`, `risk-weighted assets`, `liquidity coverage ratio`,
  `stress capital buffer`
- `real estate`: `occupancy`, `lease termination`, `tenant default`, `cap rate`
- `healthcare/regulatory`: `fda approval`, `clinical trial`, `reimbursement`, `cms`
- `supply concentration`: merge or coordinate `supplier concentration`, `sole supplier`,
  `single-source supplier`
- `customer concentration`: add `significant customer`, `top customer`, `revenue concentration`

**Implementation rules:**

- Each topic should include at least three high-precision phrases before launch.
- Single words such as `competition`, `climate`, and `labor` should be reviewed because they
  over-trigger in broad disclosure.
- Topic intensity should count topic hits plus severity words in the same section; later improve
  to count severity only within a sentence/window around the topic.

### 9. `SEVERITY_WORDS`

**Current purpose:** Increases topic intensity in diff analysis.

**Research basis:** SEC disclosure rules revolve around materiality; event studies and filing
change research suggest intensified language can matter. Severity words should modify a nearby
topic, not act as standalone topics.

**Enrichment direction:**

- Keep short and high precision.
- Split legal/accounting materiality from operational severity in a future version.

**Candidate additions to review:**

- `materially`
- `significantly`
- `severely`
- `substantially`
- `acute`
- `persistent`
- `prolonged`
- `widespread`
- `recurring`

**Do not add without context:**

- `important`, `meaningful`, `notable`; weak and subjective.

**Implementation rules:**

- Use as a multiplier only when within the same sentence or a +/- 10 token window of a topic.
- Do not count `material` in boilerplate legal headings as severity unless topic evidence exists.

### 10. `FLAG_PATTERNS`

Hard flags are not sentiment. They should be treated as event detectors with section scope,
phrase/regex rules, and audit metadata.

#### 10.1 Internal Controls Flags

Current flags:

- `material_weakness_flag`
- `significant_deficiency_flag`
- `ineffective_controls_flag`
- `restatement_flag`
- `non_reliance_flag`
- `auditor_change_flag`

**Research basis:** PCAOB AS 2201 states that effective ICFR provides reasonable assurance,
and material weaknesses prevent ICFR from being considered effective. PCAOB AS 1305 defines
significant deficiency as less severe than material weakness but important enough for oversight.

**Enrichment direction:**

- Add phrases:
  - `material weakness in internal control over financial reporting`
  - `material weaknesses in internal control over financial reporting`
  - `disclosure controls and procedures were ineffective`
  - `internal control over financial reporting was not effective`
  - `management concluded that our internal control over financial reporting was ineffective`
  - `previously issued financial statements should no longer be relied upon`
  - `will restate its financial statements`
  - `audit committee concluded`

**Implementation rules:**

- Scope to Item 9A/Item 4 first; allow Item 1A only as secondary evidence.
- Store matched phrase and section in future provenance.
- Add suppressions for `no material weakness was identified` only after testing, because some
  issuers say they remediated prior weaknesses in the same paragraph.

#### 10.2 Legal/Regulatory Flags

Current flags:

- `investigation_flag`
- `settlement_flag`
- `material_legal_proceeding_flag`

**Research basis:** Regulation S-K Item 103 covers legal proceedings; filing changes in
litigation language are important in Lazy Prices.

**Enrichment direction:**

- Add high-precision phrases:
  - `civil investigative demand`
  - `wells notice`
  - `subpoena from`
  - `received a subpoena`
  - `consent order`
  - `consent decree`
  - `cease and desist`
  - `enforcement action`
  - `settled with the sec`
  - `department of justice investigation`
  - `class action complaint`

**Implementation rules:**

- Use phrase matching and legal section scope.
- Do not use `regulatory` alone as a flag trigger.
- Add near-miss tests for `routine regulatory examinations`.

#### 10.3 Going Concern Flag

Current flag:

- `going_concern_flag`

**Research basis:** FASB ASU 2014-15 and PCAOB AS 2415 use "substantial doubt" and
"ability to continue as a going concern" language.

**Enrichment direction:**

- Add phrases:
  - `substantial doubt about our ability to continue as a going concern`
  - `substantial doubt exists`
  - `ability to continue as a going concern`
  - `unable to meet obligations as they become due`
  - `plans are intended to mitigate`
  - `substantial doubt has not been alleviated`

**Implementation rules:**

- Scope to MD&A, risk factors, footnote-like extracted text when available, and Item 8.01.
- Treat "substantial doubt has been alleviated" as still relevant but lower severity in future
  scoring; today it can remain a flag because it signals a disclosed going-concern assessment.

#### 10.4 Covenant Breach and Liquidity Flags

Current flag:

- `covenant_breach_flag`

**Research basis:** SEC MD&A guidance emphasizes liquidity, capital resources, commitments,
known demands, and cash requirements.

**Enrichment direction:**

- Add phrases:
  - `failed to comply with financial covenants`
  - `breach of financial covenant`
  - `event of default`
  - `default under our credit agreement`
  - `waiver from lenders`
  - `forbearance agreement`
  - `accelerated repayment`
  - `liquidity shortfall`
  - `insufficient liquidity`
  - `unable to refinance`

**Implementation rules:**

- Scope to MD&A, risk factors, and material agreement 8-K items.
- Use phrases; `default` alone is too broad for a hard flag.
- Add near-miss tests for accounting default settings and customer default rates.

#### 10.5 Guidance Withdrawal Flag

Current flag:

- `guidance_withdrawal_flag`

**Research basis:** Form 8-K Item 2.02 covers public announcements or releases regarding
results of operations or financial condition; guidance withdrawal is an earnings/disclosure
event often found in Item 2.02, MD&A, or earnings releases.

**Enrichment direction:**

- Add phrases:
  - `withdraws guidance`
  - `withdrawing guidance`
  - `suspended guidance`
  - `suspending guidance`
  - `no longer expects`
  - `does not expect to provide guidance`
  - `unable to provide guidance`

**Implementation rules:**

- Scope to MD&A, Item 2.02, and Item 8.01.
- Do not flag routine "we do not provide guidance" unless paired with prior guidance or
  withdrawal language.

#### 10.6 Cybersecurity Incident Flag

Current flag:

- `cybersecurity_incident_flag`

**Research basis:** SEC rules added Item 1.05 to Form 8-K for material cybersecurity incidents
and require disclosure of nature, scope, timing, and material impact or reasonably likely
material impact.

**Enrichment direction:**

- Add phrases:
  - `material cybersecurity incident`
  - `unauthorized access`
  - `ransomware attack`
  - `data exfiltration`
  - `data compromise`
  - `network intrusion`
  - `business email compromise`
  - `incident response`
  - `systems outage`
  - `personal information was accessed`
  - `reasonably likely material impact`

**Implementation rules:**

- Scope to Item 1.05, Item 1C, Item 8.01, and risk factors.
- Distinguish cyber-risk governance language from incident language. `cybersecurity` alone
  should not trigger an incident flag.
- Add tests for Item 1C governance text that should not trigger `cybersecurity_incident_flag`.

### 11. `MDNA_DENSITY_TERMS`

These are phrase packs that feed MD&A uncertainty and liquidity stress. They should remain
MD&A-scoped because Item 303 focuses on known trends and uncertainties affecting liquidity,
capital resources, and operations.

#### 11.1 `uncertainty_term_density`

**Candidate additions:**

- `known trends`
- `known uncertainties`
- `reasonably likely`
- `unable to predict`
- `cannot predict`
- `subject to change`
- `remains uncertain`
- `uncertain timing`

**Rules:**

- Phrase match first; avoid duplicating token-level uncertainty too heavily.
- Do not over-count every `may` if the section has thousands of routine forward-looking
  statements; consider capping token-only density contribution later.

#### 11.2 `demand_softness_density`

**Candidate additions:**

- `weaker demand`
- `reduced demand`
- `decline in demand`
- `order cancellations`
- `delayed orders`
- `customer destocking`
- `inventory correction`
- `lower volumes`
- `volume decline`
- `sales slowdown`

**Rules:**

- Phrase match only.
- Add industry examples for software bookings, manufacturing orders, retail traffic, and
  semiconductor inventory cycles.

#### 11.3 `margin_pressure_density`

**Candidate additions:**

- `cost inflation`
- `input cost inflation`
- `higher input costs`
- `freight costs`
- `labor costs increased`
- `pricing pressure`
- `discounting`
- `promotional activity`
- `mix shift`
- `margin compression`
- `gross margin decreased`

**Rules:**

- Phrase match only.
- Avoid generic `costs` or `inflation` alone; they are too broad.

#### 11.4 `liquidity_constraint_density`

**Candidate additions:**

- `working capital deficit`
- `negative working capital`
- `cash runway`
- `additional financing`
- `need to raise capital`
- `substantial doubt`
- `debt service`
- `near-term maturities`
- `credit facility availability`
- `borrowing base`
- `covenant compliance`
- `restricted cash`

**Rules:**

- Phrase match only.
- Coordinate with going-concern and covenant flags: density captures pressure; flags capture
  hard events.

## Recommended File Organization

Avoid one large `dictionaries.py` forever. Move toward:

```text
src/disclosure_alpha/dictionaries/
  __init__.py
  base.py                 # version, metadata, shared types
  sentiment.py            # negative, uncertainty, litigious, constraining, modal
  phrases.py              # boilerplate, MD&A density packs
  topics.py               # topic keyword packs
  flags.py                # event flags, scopes, suppressions
  external_lm.py           # optional licensed loader
```

Keep a compatibility shim so existing imports from `disclosure_alpha.dictionaries` continue
to work.

## Rollout Plan

1. Add metadata and matching tests without changing term lists.
2. Add high-precision flag and MD&A phrase expansions first.
3. Add conservative token-list expansions for negative, uncertainty, litigious, and constraining.
4. Split modal lists into weak/moderate/strong while preserving `MODAL_WORDS`.
5. Add optional external LM loader behind an environment/config flag.
6. Run validation:
   - unit tests,
   - deterministic replay,
   - false-positive review on at least 50 snippets,
   - SP100 distribution shift report before and after dictionary expansion.

See {doc}`../../appendix/changelog` for the v2 ship record (`built_in_dictionaries_v2`, `text_metrics_v2`).

## Versioning Rules

- Bump `DICTIONARY_VERSION` for any term or phrase change.
- Bump `METRICS_ENGINE_VERSION` if tokenization, matching behavior, emitted metrics, or density
  calculation changes.
- Bump `SCORING_MODEL_VERSION` only if component formulas or weights change.
- Record a changelog entry listing added/removed terms by category.

## Test Matrix

Minimum tests before shipping dictionary enrichment:

- Empty text still returns stable zeros.
- Single-word boundary tests for every token category.
- Phrase boundary tests for every phrase pack.
- Section-scope tests for every flag.
- Near-miss tests for high-risk false positives:
  - `reinvestigation` should not trigger investigation.
  - `no material weakness was identified` should not be treated the same as a disclosed weakness
    unless a prior weakness context is present.
  - Item 1C governance text should not trigger a cyber incident flag.
  - `default settings` should not trigger covenant breach.
- Distribution test:
  - Run before/after metrics on a fixed filing fixture set and review score deltas above 5 points.

## Implementation Decision Defaults

- Default runtime dictionary remains built-in and license-safe.
- Full LM-style lists are optional external data, not vendored source.
- Phrase/event categories are prioritized over broad token expansion.
- All added words require tests and a dictionary changelog.
- No global stemming or fuzzy matching in the deterministic engine.
