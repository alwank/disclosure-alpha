# pipeline

**Use when:** You want the full in-memory path from filing HTML (or EDGAR ticker) to deterministic scores in one call — or you need step-by-step control over extraction, metrics, and aggregation.

## Start here

- **`score_filing_html()`** — score local HTML; optional `prior_html` for diffs
- **`score_filing_ticker()`** — fetch from EDGAR by ticker, fiscal year, and form type
- **`compute_section_metrics()`** — extract metrics, flags, diffs without aggregating to components
- **`extract_sections_from_html()`** — section extraction only
- **`score_deterministic()`** — aggregate an existing `MetricsResult`
- **`FilingScoreResult`** — typed result with `.scores` and `.to_dict()`

## Example

```python
from disclosure_alpha import score_filing_html, score_filing_ticker

# Local HTML
result = score_filing_html(open("filing.html").read(), "10-K")
print(result.scores.overall_disclosure_risk_score)

# EDGAR (requires SEC_USER_AGENT)
result = score_filing_ticker("AAPL", 2025, form_type="10-K")
print(result.to_dict()["scores"]["components"])
```

## Custom scoring config (Python SDK)

Tune headline component weights, flag scoring constants, and v2 calibration context without forking the parser or metrics engine. Pass `config=PipelineConfig(...)` to `score_filing_html()`, `score_filing_ticker()`, `score_for_model()`, or `score_panel_tickers()`.

```python
from disclosure_alpha import PipelineConfig, ScoringConfig
from disclosure_alpha.baselines import CalibrationContext
from disclosure_alpha.pipeline import score_filing_html
from disclosure_alpha.scoring_types import COMPONENT_WEIGHTS

weights = dict(COMPONENT_WEIGHTS)
weights["disclosure_change_score"] = 0.25
weights["risk_factor_intensity_score"] = 0.10

config = PipelineConfig(
    scoring=ScoringConfig(
        config_id="change_heavy_v1",
        component_weights=weights,
    ),
    calibration_context=CalibrationContext(form_type="10-K", sector="financials"),
)
result = score_filing_html(html, "10-K", config=config)
print(result.versions["analytics_config_id"])  # change_heavy_v1
```

Default behavior is unchanged when `config` is omitted. Responses include `versions.analytics_config_id` (`builtin_default` for built-in weights).

## Full API

```{eval-rst}
.. automodule:: disclosure_alpha.pipeline
   :members: score_filing_html, score_filing_ticker, compute_section_metrics, extract_sections_from_html, score_deterministic, FilingScoreResult, MetricsResult
```
