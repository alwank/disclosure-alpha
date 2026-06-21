```mermaid
flowchart TB
  ingest["Ingest (HTML or EDGAR)"]
  extract["extract_sections_from_html()"]
  metrics["compute_section_metrics()"]
  aggregate["aggregate_deterministic_matrix()"]
  output["ScoreResult JSON"]

  ingest --> extract
  extract --> metrics
  metrics --> aggregate
  aggregate --> output

  subgraph deterministic ["Deterministic stage"]
    metrics
  end
```

Text equivalent:

```text
ingest (HTML or EDGAR)
    ↓
extract sections (Item 1A, MD&A, …)
    ↓
deterministic stage
  • text metrics (tone, boilerplate, specificity, …)
  • boolean risk flags
  • section diffs vs prior comparable filing
    ↓
aggregate
  • 9 weighted component scores (0–100)
  • overall disclosure risk score + confidence
```
