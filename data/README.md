# Parser evaluation gold set

Human-labeled filing cases used to measure **section name recall** for the deterministic section extractor (`app/core/section_extractor.py`).

## Layout

```
data/parser_eval/gold_set/
  MANIFEST.json                 # inventory + labeling status
  {accession_number}/
    labels.json                 # ground-truth section names (+ optional offsets)
    {accession_number}.html     # primary filing HTML (required to evaluate)
```

**Target (MVP):** 30 cases — 20× `10-K`, 5× `10-Q`, 5× `8-K`.

| Status | Count | Notes |
|--------|------:|-------|
| Seeded (`labeled: true`) | 10 | Bootstrap labels from parser; verify boundaries |
| Template (`labeled: false`) | 20 | Checklist only; add HTML and sections |

See `gold_set/MANIFEST.json` for the live inventory.

## `labels.json` schema

```json
{
  "filing": {
    "ticker": "AAPL",
    "cik": "0000320193",
    "accession_number": "0000320193-25-000079",
    "form_type": "10-K",
    "filing_date": "2025-10-31"
  },
  "labeled": true,
  "status": "seed",
  "labeler": "your-name",
  "labeled_at": "2026-06-18",
  "sections": [
    {
      "section_name": "item_1a_risk_factors",
      "required": true,
      "start_offset": 12345,
      "end_offset": 67890,
      "notes": "Optional reviewer note"
    }
  ]
}
```

### Section name keys (must match extractor)

Use internal keys from `app/core/dictionaries.py` → `sections_for_form_type()`:

**10-K:** `item_1a_risk_factors`, `item_3_legal_proceedings`, `item_7_mdna`, `item_7a_market_risk`, `item_9a_controls`, `item_1c_cybersecurity`

**10-Q:** `item_1a_risk_factors`, `item_2_mdna`, `item_1_legal_proceedings`, `item_4_controls`

**8-K:** `item_1_01`, `item_1_05`, `item_2_02`, `item_5_02`, `item_8_01`

Only include sections that **actually appear** in the filing. Omit items not disclosed.

Template cases may use `labeling_checklist` instead of `sections` until review is complete. Set `labeled: true` only after human verification.

## Labeling workflow

1. Open `{accession}.html` in a browser or editor.
2. For each checklist section, confirm a heading/boundary in the cleaned text (not the table of contents).
3. Add `sections[]` entries with `section_name` (required). Offsets are optional for MVP gate but help boundary audits.
4. **Boundary tolerance:** a section is correct if the extractor finds the same `section_name` and the extracted span covers the substantive body (±500 characters at boundaries is acceptable; TOC hits are incorrect).
5. Set `labeled: true`, `labeler`, and `labeled_at`.

## Adding HTML for template cases

### From local SEC cache

Ingested filings are cached at:

```
data/cache/sec_filings/{cik_without_leading_zeros}/{accession_number}.html
```

Copy into the case directory:

```bash
CIK=0000789019
ACC=0000950170-25-118967
cp "data/cache/sec_filings/${CIK#000}/$ACC.html" \
   "data/parser_eval/gold_set/$ACC/$ACC.html"
```

### Fetch via ingestion

```bash
python3.11 scripts/ingest_company.py --ticker MSFT --forms 10-Q
# then copy from data/cache/sec_filings/... as above
```

### Manual SEC download

1. Find the filing on [SEC EDGAR](https://www.sec.gov/cgi-bin/browse-edgar).
2. Open the **primary document** (`.htm` / `.html`).
3. Save as `data/parser_eval/gold_set/{accession}/{accession}.html`.
4. Respect SEC fair-access: set `SEC_USER_AGENT` in `.env` (see `.env.example`).

## Run evaluation

```bash
python3.11 scripts/eval_section_extraction.py --gold-dir data/parser_eval/gold_set
```

Writes `data/validation/reports/parser_eval_report.json`.

- Only cases with `labeled: true`, non-empty `sections`, and HTML are scored.
- Gate target: **section name accuracy ≥ 95%** (recall of expected section names).
- Template cases appear in `cases_pending` until labeled.

## Seeded cases (verify before trusting)

The 10 seed `10-K` cases were auto-labeled from `heading_boundary_v1` output. Treat them as **draft** until a reviewer confirms each boundary.
