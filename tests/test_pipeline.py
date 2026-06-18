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


def test_score_filing_ticker_mocked(monkeypatch):
    from pathlib import Path

    from disclosure_alpha.edgar.types import FilingRef
    from disclosure_alpha.pipeline import score_filing_ticker

    html_path = (
        Path(__file__).resolve().parents[1]
        / "data/parser_eval/gold_set/0000320193-25-000079/0000320193-25-000079.html"
    )
    html = html_path.read_text(encoding="utf-8", errors="replace")
    ref = FilingRef(
        cik="0000320193",
        ticker="AAPL",
        accession_number="0000320193-25-000079",
        form_type="10-K",
        fiscal_year=2025,
        quarter=None,
        filing_date="2025-10-31",
        report_date="2025-09-27",
        primary_document="aapl.htm",
    )

    monkeypatch.setattr(
        "disclosure_alpha.pipeline.load_filing_bundle",
        lambda *a, **k: __import__(
            "disclosure_alpha.pipeline", fromlist=["FilingBundle"]
        ).FilingBundle(
            ref=ref,
            html=html,
            prior_html=None,
            prior_accession=None,
        ),
    )

    result = score_filing_ticker("AAPL", 2025)
    assert result.filing["ticker"] == "AAPL"
    assert result.scores.overall_disclosure_risk_score is not None


def test_load_filing_bundle_compare_prior(monkeypatch):
    from disclosure_alpha.edgar.types import FilingRef
    from disclosure_alpha.pipeline import FilingBundle, load_filing_bundle

    ref = FilingRef(
        cik="0000320193",
        ticker="AAPL",
        accession_number="0000320193-25-000079",
        form_type="10-K",
        fiscal_year=2025,
        quarter=None,
        filing_date="2025-10-31",
        report_date="2025-09-27",
        primary_document="aapl.htm",
    )
    prior_calls: list[str] = []

    monkeypatch.setattr(
        "disclosure_alpha.edgar.resolver.resolve_filing",
        lambda *a, **k: ref,
    )
    monkeypatch.setattr(
        "disclosure_alpha.edgar.resolver.load_filing_html",
        lambda r, **k: "<html></html>",
    )

    def _prior(*a, **k):
        prior_calls.append("called")
        return ref

    monkeypatch.setattr(
        "disclosure_alpha.edgar.resolver.resolve_prior_filing",
        _prior,
    )

    bundle = load_filing_bundle("AAPL", 2025, compare_prior=True)
    assert bundle.prior_html is not None
    assert prior_calls

    prior_calls.clear()
    bundle = load_filing_bundle("AAPL", 2025, compare_prior=False)
    assert bundle.prior_html is None
    assert not prior_calls


def test_metrics_filing_ticker_mocked(monkeypatch):
    from disclosure_alpha.edgar.types import FilingRef
    from disclosure_alpha.pipeline import FilingBundle, metrics_filing_ticker

    html = """
    <html><body>
    <p>Item 1A. Risk Factors</p>
    <p>We may face litigation and regulatory investigation.</p>
    <p>Item 7. Management's Discussion and Analysis</p>
    <p>Revenue may decline amid margin pressure.</p>
    </body></html>
    """
    ref = FilingRef(
        cik="0000320193",
        ticker="AAPL",
        accession_number="0000320193-25-000079",
        form_type="10-K",
        fiscal_year=2025,
        quarter=None,
        filing_date="2025-10-31",
        report_date="2025-09-27",
        primary_document="aapl.htm",
    )
    monkeypatch.setattr(
        "disclosure_alpha.pipeline.load_filing_bundle",
        lambda *a, **k: FilingBundle(
            ref=ref, html=html, prior_html=None, prior_accession=None
        ),
    )
    result = metrics_filing_ticker("AAPL", 2025)
    assert result.filing["ticker"] == "AAPL"
    assert result.metrics.section_metrics


def test_sections_filing_ticker_mocked(monkeypatch):
    from disclosure_alpha.edgar.types import FilingRef
    from disclosure_alpha.pipeline import FilingBundle, sections_filing_ticker

    html = """
    <html><body>
    <p>Item 1A. Risk Factors</p>
    <p>We may face litigation.</p>
    </body></html>
    """
    ref = FilingRef(
        cik="0000320193",
        ticker="AAPL",
        accession_number="0000320193-25-000079",
        form_type="10-K",
        fiscal_year=2025,
        quarter=None,
        filing_date="2025-10-31",
        report_date="2025-09-27",
        primary_document="aapl.htm",
    )
    monkeypatch.setattr(
        "disclosure_alpha.pipeline.load_filing_bundle",
        lambda *a, **k: FilingBundle(
            ref=ref, html=html, prior_html=None, prior_accession=None
        ),
    )
    result = sections_filing_ticker("AAPL", 2025)
    assert result.filing["ticker"] == "AAPL"
    assert any(s.section_name == "item_1a_risk_factors" for s in result.sections)


def test_filter_metrics_result():
    from disclosure_alpha.pipeline import MetricsResult, filter_metrics_result

    metrics = MetricsResult(
        section_metrics={
            "item_1a_risk_factors": {"negative_word_ratio": 0.1},
            "item_7_mdna": {"negative_word_ratio": 0.2},
        },
        section_diffs={"item_1a_risk_factors": 50.0},
        section_flags={"item_1a_risk_factors": {"investigation_flag": True}},
        section_densities={"item_7_mdna": {"uncertainty_term_density": 10.0}},
        language_deltas={"item_1a_risk_factors": {"uncertainty_language_delta": 1.0}},
    )
    filtered = filter_metrics_result(metrics, {"item_1a_risk_factors"})
    assert set(filtered.section_metrics) == {"item_1a_risk_factors"}
    assert set(filtered.section_diffs) == {"item_1a_risk_factors"}
    assert set(filtered.section_flags) == {"item_1a_risk_factors"}
    assert filtered.section_densities == {}
    assert set(filtered.language_deltas) == {"item_1a_risk_factors"}
