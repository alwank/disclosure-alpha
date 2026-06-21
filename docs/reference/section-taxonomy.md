# Section Taxonomy

Section names are stable identifiers used in extraction, HTTP `sections=` filters, and scoring. Display names are human-readable labels.

## 10-K sections

| Section name | Display name | Required for full coverage |
|--------------|--------------|----------------------------|
| `item_1a_risk_factors` | Item 1A Risk Factors | Yes |
| `item_7_mdna` | Item 7 Management's Discussion and Analysis | Yes |
| `item_3_legal_proceedings` | Item 3 Legal Proceedings | No |
| `item_7a_market_risk` | Item 7A Market Risk | No |
| `item_9a_controls` | Item 9A Controls and Procedures | No |
| `item_1c_cybersecurity` | Item 1C Cybersecurity | No |

## 10-Q sections

| Section name | Display name | Required for full coverage |
|--------------|--------------|----------------------------|
| `item_1a_risk_factors` | Item 1A Risk Factors | Yes |
| `item_2_mdna` | Item 2 MD&A | Yes |
| `item_1_legal_proceedings` | Item 1 Legal Proceedings | No |
| `item_4_controls` | Item 4 Controls and Procedures | No |

## 8-K sections

| Section name | Display name |
|--------------|--------------|
| `item_1_01` | Item 1.01 Entry into Material Agreement |
| `item_1_05` | Item 1.05 Material Cybersecurity Incidents |
| `item_2_02` | Item 2.02 Results of Operations |
| `item_5_02` | Item 5.02 Departure of Directors |
| `item_8_01` | Item 8.01 Other Events |

## HTTP usage

Filter sections on ticker routes:

```bash
curl "http://localhost:8000/v1/company/AAPL/sections?fiscal_year=2025&sections=item_1a_risk_factors,item_7_mdna"
```

Missing required sections for a form type reduce `score_coverage_ratio` and may leave component scores as `null`. See {doc}`../methodology/overview`.

## Related

- {doc}`../guides/http/index`
- {doc}`../getting-started/concepts`
