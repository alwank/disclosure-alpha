# Disclosure Alpha

![Disclosure Alpha quickstart](https://raw.githubusercontent.com/alwank/disclosure-alpha/main/docs/assets/readme-hero-cli.png)

**Deterministic SEC filing analytics — parse, score, diff. No LLM required.**

[![PyPI](https://img.shields.io/pypi/v/disclosure-alpha.svg)](https://pypi.org/project/disclosure-alpha/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-green.svg)](LICENSE)
[![Documentation](https://readthedocs.org/projects/disclosure-alpha/badge/?version=latest)](https://disclosure-alpha.readthedocs.io/en/latest/)

Open-source, deterministic SEC filing analytics for **10-K and 10-Q** HTML. Reproducible JSON scores from text metrics, boolean risk flags, and section diffs. CLI, Python SDK, HTTP API, OpenBB Workspace, and MCP. **8-K** supported via local `--html` or MCP Builder only (not `--ticker`, EDGAR, or HTTP ticker routes).

**Not investment advice.** See [Scope and claims](https://disclosure-alpha.readthedocs.io/en/latest/getting-started/scope-and-claims.html).

## Quick start

```bash
pip install "disclosure-alpha"
export SEC_USER_AGENT="YourName your@email.com"   # required for --ticker / EDGAR only
disclosure-alpha score --ticker AAPL --fiscal-year 2025 --form 10-K
```

HTTP API + MCP: `pip install "disclosure-alpha[api,mcp]"`

```python
from disclosure_alpha import score_filing_ticker
print(score_filing_ticker("AAPL", 2025, form_type="10-K").scores.overall_disclosure_risk_score)
```

## Integration surfaces

| Surface | Entry | Extra |
|---------|-------|-------|
| CLI | `disclosure-alpha` | *(base)* |
| Python SDK | `import disclosure_alpha` | *(base)* |
| HTTP API | `disclosure-alpha-api` | `[api]` |
| OpenBB Workspace | `disclosure-alpha-api` + [OpenBB guide](https://disclosure-alpha.readthedocs.io/en/latest/guides/openbb/index.html) | `[api,mcp]` |
| MCP Analyst | `disclosure-alpha-mcp-analyst` | `[mcp]` |
| MCP Builder | `disclosure-alpha-mcp-builder` | `[mcp]` |

## Documentation

Full guides and methodology: **https://disclosure-alpha.readthedocs.io/en/latest/**

- [Installation](https://disclosure-alpha.readthedocs.io/en/latest/getting-started/installation.html)
- [Understanding scores](https://disclosure-alpha.readthedocs.io/en/latest/getting-started/understanding-scores.html)
- [HTTP API](https://disclosure-alpha.readthedocs.io/en/latest/guides/http/index.html)
- [OpenBB Workspace](https://disclosure-alpha.readthedocs.io/en/latest/getting-started/quickstart-openbb.html)
- [MCP](https://disclosure-alpha.readthedocs.io/en/latest/guides/mcp/index.html)

## Links

- **Repository:** https://github.com/alwank/disclosure-alpha
- **Changelog:** https://github.com/alwank/disclosure-alpha/blob/main/docs/appendix/changelog.md
- **Contributing:** https://github.com/alwank/disclosure-alpha/blob/main/CONTRIBUTING.md

Apache-2.0. See [LICENSE](LICENSE).
