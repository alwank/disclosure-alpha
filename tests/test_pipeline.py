import json

from disclosure_alpha.pipeline import score_filing_html


def test_score_filing_html_minimal():
    html = """
    <html><body>
    <p>Item 1A. Risk Factors</p>
    <p>We may face litigation and regulatory investigation. Results could be uncertain.</p>
    <p>Item 7. Management's Discussion and Analysis</p>
    <p>Revenue may decline amid margin pressure and liquidity constraints.</p>
    </body></html>
    """
    result = score_filing_html(html, "10-K")
    assert result.scores.overall_disclosure_risk_score is not None
    assert result.versions["parser_version"] == "section_extractor_v1"
    payload = result.to_dict()
    assert "scores" in payload
    assert json.dumps(payload)


def test_score_filing_with_prior():
    prior = "<html><body><p>Item 1A. Risk Factors</p><p>Stable operations.</p></body></html>"
    current = "<html><body><p>Item 1A. Risk Factors</p><p>We may face litigation and investigation.</p></body></html>"
    result = score_filing_html(current, "10-K", prior_html=prior)
    assert result.metrics.section_diffs.get("item_1a_risk_factors") is not None
