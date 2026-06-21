# Dictionaries

Built-in word and phrase lists in `disclosure_alpha.dictionaries`. Version: `built_in_dictionaries_v2`.

## Exported constants

| Constant | Type | Purpose |
|----------|------|---------|
| `TERM_PACK_METADATA` | `dict[str, dict]` | Audit trail per pack (source, match_type, consumers, license) |
| `NEGATIVE_WORDS` | `frozenset[str]` | Token list → `negative_word_ratio` |
| `UNCERTAINTY_WORDS` | `frozenset[str]` | Token list → `uncertainty_word_ratio` |
| `LITIGIOUS_WORDS` | `frozenset[str]` | Token list → `litigious_word_ratio` |
| `CONSTRAINING_WORDS` | `frozenset[str]` | Token list → `constraining_word_ratio` |
| `WEAK_MODAL_WORDS` | `frozenset[str]` | Modal tier (weak) |
| `MODERATE_MODAL_WORDS` | `frozenset[str]` | Modal tier (moderate) |
| `STRONG_MODAL_WORDS` | `frozenset[str]` | Modal tier (strong) |
| `MODAL_WORDS` | `frozenset[str]` | Union of modal tiers → `modal_word_ratio` |
| `BOILERPLATE_PHRASES` | `list[str]` | Phrase list → `boilerplate_phrase_ratio` |
| `GEOGRAPHY_TERMS` | `frozenset[str]` | Specificity proxy |
| `SEGMENT_TERMS` | `frozenset[str]` | Specificity proxy |
| `TOPIC_KEYWORDS` | `dict[str, list[str]]` | Diff engine topic clusters |
| `SEVERITY_WORDS` | `frozenset[str]` | Topic intensity modifier (±10 token window) |
| `FLAG_PATTERNS` | `dict[str, list[str]]` | Boolean section flags |
| `FLAG_SECTION_SCOPE` | `dict[str, frozenset[str]]` | Per-flag section allowlist |
| `MDNA_DENSITY_TERMS` | `dict[str, list[str]]` | MD&A phrase density packs |
| `SUPPORTED_SECTIONS_*` | `dict[str, str]` | Section regex maps by form type |
| `REQUIRED_SECTIONS` | `dict[str, list[str]]` | Minimum sections per form |

## `TERM_PACK_METADATA` shape

Each pack entry includes:

```python
{
    "source": "built_in_finance_curated",  # or sec_pcaob_fasb_phrase_curated for flags
    "match_type": "token" | "phrase",
    "consumer": ["metric_or_score_name", ...],
    "license": "repo_safe_manual_curation",
}
```

Metadata is documentation-only; runtime matching uses the constant lists above.

## Matching helpers

Phrase and token matching logic lives in `disclosure_alpha.text_matching` (shared by `text_metrics` and `diff_engine`).

## Related

- {doc}`../../methodology/metrics-engine`
- {doc}`../../appendix/changelog`
