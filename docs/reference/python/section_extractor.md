# section_extractor

**Use when:** You have raw SEC filing HTML and need structured sections (Item 1A, MD&A, controls) before metrics or scoring.

## Start here

- **`extract_sections()`** — parse a `FilingDocument` into `ExtractedSection` list
- **`FilingDocument`** — wrapper for HTML + form type + metadata
- **`ExtractedSection`** — section name, cleaned text, confidence, warnings
- **`required_sections_present()`** — check whether 10-K / 10-Q required sections extracted

For a one-liner from HTML string, use `extract_sections_from_html()` in {doc}`pipeline`.

Required section names for full coverage: `item_1a_risk_factors` + `item_7_mdna` (10-K) or `item_2_mdna` (10-Q). See {doc}`../section-taxonomy`.

## Example

```python
from disclosure_alpha import FilingDocument, extract_sections, required_sections_present

doc = FilingDocument(html=open("filing.html").read(), form_type="10-K")
sections = extract_sections(doc)
print([s.section_name for s in sections])
print(required_sections_present("10-K", sections))
```

## Full API

```{eval-rst}
.. automodule:: disclosure_alpha.section_extractor
   :members: extract_sections, FilingDocument, ExtractedSection, required_sections_present
```
