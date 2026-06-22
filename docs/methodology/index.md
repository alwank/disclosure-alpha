# How Scoring Works

This section explains how Disclosure Alpha computes deterministic disclosure risk scores from SEC filing text — what the open-source pipeline does today, not planned features.

**Read this order:**

1. {doc}`overview`
2. {doc}`../getting-started/understanding-scores`
3. {doc}`../validation/evidence-and-limitations`
4. Detailed specs below (metrics, diff, aggregation)

For supported claims and limitations, see {doc}`../getting-started/scope-and-claims`.

```{toctree}
:maxdepth: 2

overview
research-foundation
```

## Implementation details

Technical reference for each pipeline stage:

```{toctree}
:maxdepth: 1
:caption: Specifications

metrics-engine
diff-engine
aggregation
```
