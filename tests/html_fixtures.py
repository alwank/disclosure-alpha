from pathlib import Path


def minimal_10k_html() -> str:
    return """
    <html><body>
    <p>Item 1A. Risk Factors</p>
    <p>We may face litigation and regulatory investigation. Results could be uncertain.</p>
    <p>Item 7. Management's Discussion and Analysis</p>
    <p>Revenue may decline amid margin pressure and liquidity constraints.</p>
    </body></html>
    """


def minimal_prior_html() -> str:
    return """
    <html><body>
    <p>Item 1A. Risk Factors</p>
    <p>Stable operations continue without material litigation.</p>
    <p>Item 7. Management's Discussion and Analysis</p>
    <p>Revenue remained stable with modest margin improvement.</p>
    </body></html>
    """


def write_temp_html(tmp_path: Path, content: str, name: str = "filing.html") -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path
