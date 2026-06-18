from pathlib import Path

from disclosure_alpha.section_extractor import FilingDocument, extract_sections


FIXTURE = Path(__file__).parent / "fixtures" / "sample_10k.html"


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
