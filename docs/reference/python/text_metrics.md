# text_metrics

**Use when:** You need per-section tone ratios, specificity scores, boolean flags, or MD&A density packs — the raw signals that feed component scores.

## Start here

- **`compute_text_metrics()`** — tone ratios, specificity, boilerplate, readability for one section
- **`detect_section_flags()`** — boolean risk flags scoped by section name
- **`compute_density_metrics()`** — MD&A keyword densities (`item_7_mdna`, `item_2_mdna`)
- **`SectionTextInput`** / **`TextMetricResult`** — input and output types

In the pipeline, `compute_section_metrics()` calls these for every extracted section. Ratio fields map to components via {doc}`../../methodology/aggregation` (e.g. `negative_word_ratio` → `risk_factor_intensity_score`).

## Example

```python
from disclosure_alpha.text_metrics import SectionTextInput, compute_text_metrics, detect_section_flags

inp = SectionTextInput("item_1a_risk_factors", cleaned_text)
metrics = compute_text_metrics(inp)
flags = detect_section_flags(cleaned_text, "item_1a_risk_factors")
print(metrics.negative_word_ratio, flags["investigation_flag"])
```

## Full API

```{eval-rst}
.. automodule:: disclosure_alpha.text_metrics
   :members: compute_text_metrics, detect_section_flags, compute_density_metrics, SectionTextInput, TextMetricResult
```
