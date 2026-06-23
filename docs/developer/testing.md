# Testing

**Audience:** Contributors running or extending the test suite.

## Summary

How to run unit, integration, and validation checks locally and what CI enforces.

## In plain terms

Fast tests run without network access. Integration and EDGAR-backed tests are opt-in. Full validation harness (scripts, reports) lives on the internal branch — see `INTERNAL_VALIDATION.md`.

## Main content

From the repository root:

```bash
# Default CI-equivalent unit tests
pytest -q -m "not integration" --cov=disclosure_alpha --cov-fail-under=75

# Optional integration (network / EDGAR)
export SEC_USER_AGENT="YourName your@email.com"
RUN_INTEGRATION=1 pytest -q -m integration
```

Construct-validity tests: `tests/test_construct_validity.py`, `tests/test_matrix_validation.py`. See {doc}`../getting-started/scope-and-claims` for public evidence claims.

## Related

- {doc}`architecture` — package layout and surfaces
- Repository [CONTRIBUTING.md](https://github.com/alwank/disclosure-alpha/blob/main/CONTRIBUTING.md)
