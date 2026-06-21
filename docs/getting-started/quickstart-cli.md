# Quickstart: CLI

Score a filing from the terminal in under a minute.

**Audience:** Terminal users and script writers.
**Before you start:** {doc}`installation`; {doc}`sec-edgar-setup` for `--ticker`.

## Summary

Run `disclosure-alpha score` to print deterministic score JSON to stdout.

## Local HTML

**Goal:** Score a filing you already have on disk — no network required.

```bash
disclosure-alpha extract --html filing.html --form 10-K
disclosure-alpha score --html filing.html --form 10-K
disclosure-alpha score --html current.html --form 10-K --prior-html prior.html
```

### Sample output

Scores block from a minimal synthetic 10-K (trimmed fixture):

```{literalinclude} ../examples/score-minimal-10k.json
:language: json
:lines: 124-145
```

### How to read it

- **`overall_disclosure_risk_score`** — headline 0–100; see {doc}`understanding-scores`
- **`score_coverage_ratio`** — fraction of headline components computed
- **`missing_components`** — often `disclosure_change_score` when no `--prior-html` is supplied

### If something looks wrong

Low coverage or null change scores: {doc}`faq`.

## By ticker + fiscal year

**Goal:** Fetch from EDGAR and score in one command.

```bash
export SEC_USER_AGENT="YourName your@email.com"
disclosure-alpha score --ticker AAPL --fiscal-year 2025 --form 10-K
disclosure-alpha score --ticker MSFT --fiscal-year 2025 --form 10-Q --quarter Q2
```

### Sample output

Same JSON shape as local HTML. Filter with `jq`:

```bash
disclosure-alpha score --ticker AAPL --fiscal-year 2025 | jq '.scores.overall_disclosure_risk_score'
```

### How to read it

- Compare **`overall_disclosure_risk_score`** across tickers — not a buy/sell signal
- Check **`versions`** if scores differ from a previous run
- Inspect **`components`** for which language signals drove the headline

### If something looks wrong

EDGAR errors and null components: {doc}`faq`.

## Related

- {doc}`understanding-scores` — interpret score JSON
- {doc}`../guides/cli/index` — full command reference
- {doc}`../methodology/overview`
