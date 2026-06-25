from pathlib import Path
from unittest.mock import MagicMock, patch

from disclosure_alpha.dictionaries.base import SECTION_HEADING_SPECS
from disclosure_alpha.section_extractor import (
    FilingDocument,
    _parse_blocks,
    _sec_parser_class,
    extract_sections,
    required_sections_present,
)
from disclosure_alpha.version import PARSER_VERSION


FIXTURE = Path(__file__).parent / "fixtures" / "sample_10k.html"
FILING_FIXTURES = Path(__file__).parent / "fixtures" / "filings"


def test_section_heading_specs_single_source():
    from disclosure_alpha.dictionaries.base import SUPPORTED_SECTIONS_10K

    assert set(SECTION_HEADING_SPECS) >= set(SUPPORTED_SECTIONS_10K)
    item, title = SECTION_HEADING_SPECS["item_1a_risk_factors"]
    assert item == "1A"
    assert title == "risk factors"


def test_sec_parser_class_selects_by_form_type():
    import sec_parser as sp

    assert _sec_parser_class("10-Q") is sp.Edgar10QParser
    assert _sec_parser_class("10-Q/A") is sp.Edgar10QParser
    assert _sec_parser_class("8-K") is sp.Edgar10QParser

    ten_k_cls = _sec_parser_class("10-K")
    if hasattr(sp, "Edgar10KParser"):
        assert ten_k_cls is sp.Edgar10KParser
    else:
        assert ten_k_cls is sp.Edgar10QParser


def test_sec_parser_class_10k_when_available():
    fake_10k = MagicMock(name="Edgar10KParser")
    fake_10q = MagicMock(name="Edgar10QParser")
    fake_sp = MagicMock(Edgar10KParser=fake_10k, Edgar10QParser=fake_10q)

    with patch.dict("sys.modules", {"sec_parser": fake_sp}):
        assert _sec_parser_class("10-K") is fake_10k
        assert _sec_parser_class("10-Q") is fake_10q


def test_parse_blocks_passes_form_type_to_parser():
    parser_instance = MagicMock()
    parser_instance.parse.return_value = []
    parser_cls = MagicMock(return_value=parser_instance)

    with patch(
        "disclosure_alpha.section_extractor._sec_parser_class",
        return_value=parser_cls,
    ):
        blocks, warning = _parse_blocks("<html></html>", form_type="10-K")

    assert blocks == []
    assert warning is None
    parser_cls.assert_called_once()
    parser_instance.parse.assert_called_once_with("<html></html>")


def test_extract_sections_stamps_sec_parser_unavailable_warning():
    html = FIXTURE.read_text(encoding="utf-8")
    with patch(
        "disclosure_alpha.section_extractor._parse_blocks",
        return_value=([], "sec_parser_unavailable"),
    ):
        sections = extract_sections(
            FilingDocument(cik="1", accession_number="x", form_type="10-K", html=html)
        )
    assert sections
    assert "sec_parser_unavailable" in sections[0].warnings


def test_extract_sections_passes_form_type_to_parse_blocks():
    html = FIXTURE.read_text(encoding="utf-8")
    with patch(
        "disclosure_alpha.section_extractor._parse_blocks",
        wraps=_parse_blocks,
    ) as mock_parse:
        extract_sections(
            FilingDocument(cik="1", accession_number="x", form_type="10-Q", html=html)
        )
        mock_parse.assert_called_once()
        assert mock_parse.call_args.kwargs["form_type"] == "10-Q"


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
    assert item_1a.extraction_method == "sec_parser_sequence_v1"
    assert item_1a.parser_version == PARSER_VERSION
    assert "competition" in item_1a.cleaned_text.lower()


def test_missing_section_not_fabricated():
    html = "<html><body><p>Item 7. Management's Discussion</p><p>Only MDNA here.</p></body></html>"
    sections = extract_sections(
        FilingDocument(cik="1", accession_number="x", form_type="10-K", html=html)
    )
    names = {s.section_name for s in sections}
    assert "item_1a_risk_factors" not in names


def test_present_sections_lack_missing_required_warning():
    body = "Competition and regulatory risk may adversely affect operations. " * 80
    html = f"""
    <html><body>
    <h1>Item 1A. Risk Factors</h1>
    <p>{body}</p>
    </body></html>
    """
    sections = extract_sections(
        FilingDocument(cik="1", accession_number="x", form_type="10-K", html=html)
    )
    assert "item_7_mdna" not in {s.section_name for s in sections}
    assert not required_sections_present("10-K", sections)
    for section in sections:
        assert "missing_required_section" not in section.warnings


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


def test_fallback_picks_substantive_body_heading():
    body = "Competition and regulatory risk may adversely affect operations. " * 80
    html = f"""
    <html><body>
    <p>Table of Contents</p>
    <p>Item 1A. Risk Factors .......... 5</p>
    <p>Item 7. Management's Discussion .......... 20</p>
    <h1>Item 1A. Risk Factors</h1>
    <p>{body}</p>
    <h1>Item 7. Management's Discussion and Analysis</h1>
    <p>Revenue may fluctuate due to market volatility.</p>
    </body></html>
    """
    sections = extract_sections(FilingDocument("1", "x", "10-K", html))
    item_1a = next(s for s in sections if s.section_name == "item_1a_risk_factors")
    assert item_1a.word_count >= 200
    assert "Competition and regulatory risk" in item_1a.cleaned_text


def test_finalize_confidence_long_slice():
    from disclosure_alpha.section_extractor import _finalize_confidence

    assert _finalize_confidence(0.5, 5000, []) >= 0.85
    assert _finalize_confidence(0.5, 250, []) >= 0.76


def test_short_slice_stays_low_confidence():
    from disclosure_alpha.section_extractor import _finalize_confidence

    assert _finalize_confidence(0.9, 30, ["short_section"]) <= 0.35


def test_item1a_last_resort_clean_html():
    from disclosure_alpha.section_extractor import _extract_item1a_from_clean_html

    body = "Operational and competitive risks are described herein. " * 60
    html = f"""
    <html><body>
    <div>ITEM 1A. RISK FACTORS</div>
    <p>{body}</p>
    <div>Item 1B. Unresolved Staff Comments</div>
    <p>None.</p>
    </body></html>
    """
    doc = FilingDocument("1", "x", "10-K", html)
    sec = _extract_item1a_from_clean_html(doc, "test_v")
    assert sec is not None
    assert sec.word_count >= 200
    assert sec.extraction_method == "clean_html_last_resort"


def test_pick_best_extraction_prefers_longer_fallback():
    from disclosure_alpha.section_extractor import ExtractedSection, _pick_best_extraction

    primary = ExtractedSection(
        "item_1a_risk_factors", "short", "short", "h1", 10, 1, 0.35,
        "sec_parser_sequence_v1", "v", warnings=["short_section"],
    )
    fallback = ExtractedSection(
        "item_1a_risk_factors", "x " * 300, "x " * 300, "h2", 300, 5, 0.85,
        "heading_boundary_fallback", "v",
    )
    merged = _pick_best_extraction(primary, fallback)
    assert merged is not None
    assert merged.word_count >= 200
    assert merged.extraction_method == "heading_boundary_fallback_merged"
