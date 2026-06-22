# First Successful Run

One path from install to a working score — no EDGAR required for the first command.

## 1. Check Python

Requires **Python 3.11+**:

```bash
python3 --version
```

## 2. Install

```bash
pip install "disclosure-alpha"
disclosure-alpha --help
```

## 3. Score local HTML (no network)

Use the committed sample fixture (clone the repo or copy the file):

```bash
disclosure-alpha score --html tests/fixtures/sample_10k.html --form 10-K \
  | jq '{overall: .scores.overall_disclosure_risk_score, coverage: .scores.score_coverage_ratio}'
```

**Expected output** (shape; values may vary slightly by release):

```json
{
  "overall": 17.84,
  "coverage": 0.7778
}
```

Full JSON includes `scores.components`, `sections`, `versions`, and `flags`. See {doc}`understanding-scores` and {doc}`../reference/score-catalog`.

## 4. Score by ticker (requires EDGAR)

```bash
export SEC_USER_AGENT="YourName your@email.com"
disclosure-alpha score --ticker AAPL --fiscal-year 2025 --form 10-K \
  | jq '.scores.overall_disclosure_risk_score'
```

You should see a single number (typically 0–100). First fetch may take a few seconds.

## If this fails

| Symptom | Fix |
|---------|-----|
| `command not found: disclosure-alpha` | Use the same Python env as `pip install`; add `~/.local/bin` to `PATH` |
| `SEC_USER_AGENT` / EDGAR error | Set `export SEC_USER_AGENT="YourName your@email.com"` — see {doc}`sec-edgar-setup` |
| Filing not found | Check ticker, fiscal year, and form type; try another ticker |
| Low `score_coverage_ratio` or many `null` components | Missing sections or no prior filing — see {doc}`faq` |

## Next steps

- {doc}`quickstart-cli` — full CLI reference
- {doc}`quickstart-python` — same workflow in Python
- {doc}`choose-your-surface` — HTTP API or MCP
