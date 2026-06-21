# Core Concepts

**Audience:** New users who want a mental model before scoring.
**Before you start:** None — this is the first conceptual stop after install.

## Summary

What Disclosure Alpha does and how scores flow from filing HTML to JSON — without repeating the full score walkthrough.

## In plain terms

Disclosure Alpha reads SEC filing HTML and compares language patterns and year-over-year section changes to produce reproducible disclosure risk scores. You get JSON with an overall score, nine component scores, and coverage signals — no LLM required.

## Pipeline

```{include} ../_includes/pipeline-diagram.md
```

See {doc}`../methodology/overview` for component families and prior-filing rules.

## Scores and components

Component names, plain-English meanings, and the 0–100 scale are documented in one place: {doc}`understanding-scores`.

## Evidence & limitations

Scores are validated on a fixed S&P 500 FY2025 corpus — not a trading signal. See {doc}`../validation/evidence-and-limitations` for supported claims and known limits.

## Related

- {doc}`understanding-scores` — read a score response
- {doc}`choose-your-surface`
- {doc}`../methodology/overview`
- {doc}`../guides/index`
