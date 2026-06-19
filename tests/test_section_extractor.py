from pathlib import Path

from disclosure_alpha.section_extractor import (
    FilingDocument,
    extract_sections,
    required_sections_present,
)


FIXTURE = Path(__file__).parent / "fixtures" / "sample_10k.html"
FILING_FIXTURES = Path(__file__).parent / "fixtures" / "filings"


def test_extract_item_1a_and_item_7():
    html = FIXTURE.read_text(encoding="utf-8")
    sections = extract_sections(
        FilingDocument(cik="0000320193", accession_number="x", form_type="10-K", html=html)
    )
    names = {s.section_name for s in sections}
    assert "item_1a_risk_factors" in names
    assert "item_7_mdna" in names
    item_1a = next(s for s in sections if s.section_name == "item_1a_risk_factors")
    assert item_1a.word_count > 20
    assert item_1a.extraction_confidence > 0.3
    assert item_1a.extraction_method == "sec_parser_sequence_v2"
    assert item_1a.parser_version == "section_extractor_v2"
    assert "competition" in item_1a.cleaned_text.lower()


def test_missing_section_not_fabricated():
    html = "<html><body><p>Item 7. Management's Discussion</p><p>Only MDNA here.</p></body></html>"
    sections = extract_sections(
        FilingDocument(cik="1", accession_number="x", form_type="10-K", html=html)
    )
    names = {s.section_name for s in sections}
    assert "item_1a_risk_factors" not in names


def test_malformed_html_does_not_crash():
    sections = extract_sections(
        FilingDocument(cik="1", accession_number="x", form_type="10-K", html="<html><body>")
    )
    assert isinstance(sections, list)


def test_toc_entries_ignored_when_body_headings_exist():
    html = """
    <html><body>
    <p>Table of Contents</p>
    <p>Item 1A. Risk Factors .............. 12</p>
    <p>Item 7. Management's Discussion and Analysis .............. 30</p>
    <h1>Item 1A. Risk Factors</h1>
    <p>Competition and regulatory uncertainty may adversely affect operations.</p>
    <p>Supply chain disruptions may adversely affect our business from time to time.</p>
    <h1>Item 7. Management's Discussion and Analysis</h1>
    <p>Revenue may fluctuate due to market volatility and liquidity constraints.</p>
    </body></html>
    """
    sections = extract_sections(FilingDocument("1", "x", "10-K", html))
    names = [s.section_name for s in sections]
    assert names[:2] == ["item_1a_risk_factors", "item_7_mdna"]
    assert "Table of Contents" not in sections[0].cleaned_text


def test_duplicate_heading_chooses_substantive_body():
    html = """
    <html><body>
    <p>Item 1A. Risk Factors .............. 12</p>
    <h1>Item 1A. Risk Factors</h1>
    <p>Actual risk factor language includes competition, litigation, liquidity,
    uncertainty, cybersecurity, and operational disruption concerns.</p>
    </body></html>
    """
    sections = extract_sections(FilingDocument("1", "x", "10-K", html))
    assert len([s for s in sections if s.section_name == "item_1a_risk_factors"]) == 1
    assert "Actual risk factor language" in sections[0].cleaned_text


def test_item_7_does_not_absorb_item_7a():
    html = """
    <html><body>
    <h1>Item 7. Management's Discussion and Analysis</h1>
    <p>Management discusses revenue, margins, demand, liquidity, cash flows,
    and market conditions in this section.</p>
    <h1>Item 7A. Quantitative and Qualitative Disclosures About Market Risk</h1>
    <p>We are exposed to interest rate and foreign currency market risks.</p>
    </body></html>
    """
    sections = extract_sections(FilingDocument("1", "x", "10-K", html))
    by_name = {s.section_name: s for s in sections}
    assert "item_7_mdna" in by_name
    assert "item_7a_market_risk" in by_name
    assert "Quantitative and Qualitative" not in by_name["item_7_mdna"].cleaned_text


def test_10q_sections_route_correctly():
    html = """
    <html><body>
    <h1>Item 1. Legal Proceedings</h1>
    <p>Legal proceedings discussion with investigation litigation claims.</p>
    <h1>Item 1A. Risk Factors</h1>
    <p>Risk factors may include competition liquidity uncertainty and disruption.</p>
    <h1>Item 2. Management Discussion</h1>
    <p>Management discussion covers revenue, margins, liquidity, and operations.</p>
    <h1>Item 4. Controls and Procedures</h1>
    <p>Controls and procedures were evaluated by management.</p>
    </body></html>
    """
    names = {
        s.section_name
        for s in extract_sections(FilingDocument("1", "x", "10-Q", html))
    }
    assert names == {
        "item_1_legal_proceedings",
        "item_1a_risk_factors",
        "item_2_mdna",
        "item_4_controls",
    }


def test_8k_sections_route_correctly():
    html = """
    <html><body>
    <h1>Item 1.01</h1><p>Entry into material definitive agreement.</p>
    <h1>Item 1.05</h1><p>Material cybersecurity incident discussion.</p>
    <h1>Item 2.02</h1><p>Results of operations and financial condition.</p>
    <h1>Item 5.02</h1><p>Departure or appointment of directors or officers.</p>
    <h1>Item 8.01</h1><p>Other events and additional disclosure.</p>
    </body></html>
    """
    names = {s.section_name for s in extract_sections(FilingDocument("1", "x", "8-K", html))}
    assert names == {"item_1_01", "item_1_05", "item_2_02", "item_5_02", "item_8_01"}


def test_real_filing_regression_fixtures():
    cases = {
        "aapl_2025_10k.html": {
            "item_1a_risk_factors",
            "item_1c_cybersecurity",
            "item_3_legal_proceedings",
            "item_7_mdna",
            "item_7a_market_risk",
            "item_9a_controls",
        },
        "tgt_2026_10k.html": {
            "item_1a_risk_factors",
            "item_1c_cybersecurity",
            "item_3_legal_proceedings",
            "item_7_mdna",
            "item_7a_market_risk",
            "item_9a_controls",
        },
        "amzn_2026_10k.html": {
            "item_1a_risk_factors",
            "item_1c_cybersecurity",
            "item_3_legal_proceedings",
            "item_7_mdna",
            "item_7a_market_risk",
            "item_9a_controls",
        },
    }
    for filename, expected in cases.items():
        html = (FILING_FIXTURES / filename).read_text(encoding="utf-8", errors="replace")
        sections = extract_sections(FilingDocument("1", filename, "10-K", html))
        names = {s.section_name for s in sections}
        assert expected <= names
        assert required_sections_present("10-K", sections)
        assert all(s.word_count >= 50 for s in sections)
        assert min(s.extraction_confidence for s in sections) >= 0.75
