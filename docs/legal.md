# Legal and Disclaimer

## Not investment advice

Disclosure Alpha produces deterministic analytics from SEC filing text. Output is for **research, integration testing, and disclosure monitoring** — not investment, legal, or accounting advice. Read the underlying filings before making decisions.

## SEC EDGAR

Ticker-based commands fetch data from [SEC EDGAR](https://www.sec.gov/edgar). You must:

- Set a proper `SEC_USER_AGENT` (see {doc}`getting-started/sec-edgar-setup`)
- Comply with SEC [fair access](https://www.sec.gov/os/webmaster-faq#code-support) policy
- Review SEC terms of use before redistributing bulk-downloaded filings

Production deployment notes: {doc}`guides/production`.

## Validation scope

Empirical checks on the current release are summarized in {doc}`validation/evidence-and-limitations` and {doc}`getting-started/scope-and-claims`.

## Open-source license

Disclosure Alpha is licensed under **Apache-2.0**. See the `LICENSE` file in the repository.

Third-party data (SEC filings, market data used in optional validation extras) remains subject to its own terms.

## Product surfaces

This repository ships CLI, Python SDK, HTTP API, and MCP entry points you run locally or on your infrastructure. See {doc}`getting-started/choose-your-surface`.

## Related

- {doc}`validation/evidence-and-limitations`
- {doc}`getting-started/scope-and-claims`
- {doc}`guides/production`
- {doc}`getting-started/faq`
