# Understanding Scores

**Audience:** Anyone interpreting CLI, Python, or HTTP score JSON for the first time.
**Before you start:** Skim {doc}`concepts` for pipeline vocabulary.

## Summary

How to read Disclosure Alpha's 0–100 disclosure risk scores, component fields, and coverage signals.

```{admonition} Default scoring model
:class: note

Examples on this page and all committed fixtures use **`deterministic_scoring_v1`**. CLI, HTTP, and MCP default to v1. An opt-in **`deterministic_scoring_v2`** exists for Python (`score_deterministic_v2`); see {doc}`../reference/versioning`. Do not compare v1 and v2 numeric levels without re-scoring.
```

## Higher / lower means

| Field | Higher (toward 100) | Lower (toward 0) |
|-------|---------------------|------------------|
| `overall_disclosure_risk_score` | More concern from weighted language/change signals | Less concern |
| `boilerplate_risk_score` | More vague / boilerplate language | More specific language |
| `specificity_quality_score` | **Better** specificity (directionally opposite of most risk scores) | Weaker specificity |
| `disclosure_change_score` | Larger year-over-year section change | Smaller change |
| `score_coverage_ratio` | More headline components computed | More gaps (null components) |

Version and evidence context: {doc}`../reference/versioning`, {doc}`../validation/evidence-and-limitations`.

## In plain terms

Disclosure Alpha compares filing language patterns and year-over-year section changes to produce reproducible risk scores — no LLM required. The headline number is a weighted blend of nine headline-weighted component scores; `specificity_quality_score` is also returned but excluded from headline weights. Lower coverage or missing prior filings show up as null components and a lower `score_coverage_ratio`.

## Problem framing

You want to compare a company's disclosure language against its prior filing — or against a peer screen — without hand-reading every risk-factor paragraph. Disclosure Alpha extracts Item 1A, MD&A, and other sections, runs deterministic text metrics and diffs, and returns a single JSON object you can sort, filter, or wire into dashboards.

## Score anatomy

```mermaid
flowchart TB
  html["Filing HTML"]
  sections["Section extraction"]
  metrics["Text metrics + flags"]
  diffs["Section diffs vs prior"]
  components["Ten computed scores (9 headline)"]
  overall["overall_disclosure_risk_score"]

  html --> sections
  sections --> metrics
  sections --> diffs
  metrics --> components
  diffs --> components
  components --> overall
```

```{include} ../_includes/pipeline-diagram.md
```

## Reading a response

The sample below comes from a minimal synthetic 10-K with no prior filing. Section text is trimmed in the committed fixture; full structure: [`score-minimal-10k.json`](../examples/score-minimal-10k.json).

```{literalinclude} ../examples/score-minimal-10k.json
:language: json
:lines: 124-151
```

### Headline fields

- **`overall_disclosure_risk_score`** (~18 here) — weighted mean of present headline components. On the scale below, this filing is low concern.
- **`score_coverage_ratio`** (0.78) — seven of nine headline components computed. Names in `missing_components` were not computed.
- **`confidence_score`** (0.44) — lower here because extraction confidence is weak on a tiny synthetic filing and there is no prior for change diffs.

### Top components in this example

- **`legal_regulatory_risk_score`** (25.3) — litigious tone in Item 1A plus an investigation flag.
- **`boilerplate_risk_score`** (42.5) — moderate vague-language signal relative to other components.
- **`mdna_uncertainty_score`** (26.7) — uncertainty language and margin-pressure density in MD&A.

`disclosure_change_score` and `event_severity_score` are **null** because no prior filing was supplied — that means missing, not zero change.

When a prior filing is available, the scores block looks like this (abbreviated):

```{literalinclude} ../examples/score-with-prior-snippet.json
:language: json
```

Here `disclosure_change_score` is present and coverage rises when MD&A and prior filing are both available.

Full coverage (all nine headline components) with prior + Item 1A + MD&A:

```{literalinclude} ../examples/score-full-coverage-snippet.json
:language: json
```

## Component guide

```{include} ../_includes/component-plain-english.md
```

## Score scale

```{include} ../_includes/score-scale.md
```

## Low coverage and null components

When required sections fail to extract or there is no prior comparable filing:

- Affected components appear as **`null`** in `components` (never substituted with zero).
- **`missing_components`** lists component names that could not be computed.
- **`score_coverage_ratio`** drops; the headline score renormalizes over present components only.

See {doc}`faq` for troubleshooting low coverage and null change scores.

## Related

- {doc}`concepts` — pipeline vocabulary
- {doc}`../reference/versioning` — artifact versions and v1 → v2 migration
- {doc}`../methodology/overview` — full specification
- {doc}`../reference/score-catalog` — component catalog and weights
- {doc}`../validation/evidence-and-limitations` — supported claims
- {doc}`../appendix/glossary` — terms and artifact versions
