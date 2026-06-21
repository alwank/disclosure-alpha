# diff_engine

**Use when:** You have current and prior section text and need change scores, topic lists, or language deltas — typically as part of a prior-filing comparison workflow.

## Start here

- **`compute_section_diff()`** — full diff result including `disclosure_change_score` and `language_deltas`
- **`SectionDiffResult`** — typed output with similarities, topics, and confidence
- **`lexical_similarity()`** — TF-IDF cosine similarity helper

Prior text is required for meaningful change scores. No prior → `disclosure_change_score` is `null`. See {doc}`../../getting-started/faq`.

## Example

```python
from disclosure_alpha.diff_engine import compute_section_diff

diff = compute_section_diff(
    current_text="We may face litigation and regulatory investigation.",
    prior_text="We operate in a competitive market.",
    section_name="item_1a_risk_factors",
)
print(diff.disclosure_change_score, diff.new_topics)
```

## Full API

```{eval-rst}
.. automodule:: disclosure_alpha.diff_engine
   :members: compute_section_diff, SectionDiffResult, lexical_similarity, extract_topics
```
