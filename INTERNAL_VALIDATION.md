# Internal validation harness

The public `main` branch ships the product and public evidence ([Evidence and validation](https://disclosure-alpha.readthedocs.io/en/latest/getting-started/evidence.html), [Scope and claims](https://disclosure-alpha.readthedocs.io/en/latest/getting-started/scope-and-claims.html)). The full validation harness — scripts, reports, baselines, and reproduction docs — lives on the **`internal`** branch.

## Use the internal branch

```bash
git fetch origin internal
git checkout internal
git push -u origin internal   # first time only, from a machine with the branch
```

That branch includes:

- `scripts/validate_*.py`, `scripts/build_validation_corpus*.py`, and related EDGAR/outcome tooling
- `data/validation/README.md`, `reports/`, and `baselines/`
- `docs/validation/` (gate tables and reproduction notes)

## Stay on public main for product work

```bash
git checkout main
```

Validation scripts and reports are gitignored on `main` so they do not appear in public clones or GitHub release archives. Re-run harness steps from the `internal` branch when you need to refresh evidence locally.

## Refreshing evidence

After a scoring or dictionary change on `internal`:

1. Rebuild corpora per `data/validation/README.md`
2. Regenerate reports under `data/validation/reports/`
3. Copy headline numbers into `docs/getting-started/evidence.md` and the **Research-backed** table in `README.md` on `main` if the public claim changes.

Do not commit internal gate pass/fail tables to public docs — only the supported headline metric and cohort size.
