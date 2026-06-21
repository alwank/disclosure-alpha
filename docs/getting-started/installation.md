# Installation

Install Disclosure Alpha with **Python 3.11+**.

## From PyPI

Install from [PyPI](https://pypi.org/project/disclosure-alpha/):

```bash
pip install "disclosure-alpha"
```

HTTP API and MCP together:

```bash
pip install "disclosure-alpha[api,mcp]"
```

Pin a release when reproducibility matters:

```bash
pip install "disclosure-alpha==1.0.1[api,mcp]"
```

## Optional extras

| Extra | Purpose |
|-------|---------|
| *(base)* | CLI + Python SDK |
| `api` | HTTP API (`disclosure-alpha-api`) |
| `mcp` | MCP servers for Cursor / Claude Desktop |
| `dev` | pytest tooling (contributors) |
| `semantic` | MiniLM embeddings (default pipeline uses TF-IDF) |
| `validation` | Construct-validity harness (spaCy) |
| `outcomes` | L3 outcome fetch (yfinance) |

```bash
pip install "disclosure-alpha[api]"
pip install "disclosure-alpha[mcp]"
pip install "disclosure-alpha[api,mcp]"
```

## From source (contributors)

```bash
git clone https://github.com/alwank/disclosure-alpha.git
cd disclosure-alpha
pip install -e ".[api,mcp,dev]"
```

## Verify entry points

```bash
disclosure-alpha --help
disclosure-alpha-api --help   # requires [api]
disclosure-alpha-mcp-analyst --help   # requires [mcp]
```

## Next steps

- {doc}`sec-edgar-setup` — required for ticker-based commands
- {doc}`faq` — common errors and fixes
- {doc}`quickstart-cli` — score from the terminal
- {doc}`quickstart-python` — score from Python
- {doc}`choose-your-surface` — pick CLI, Python, HTTP, or MCP
