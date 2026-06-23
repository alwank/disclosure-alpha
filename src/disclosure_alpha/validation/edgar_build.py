"""EDGAR-backed worker helpers for validation corpus builders."""

from __future__ import annotations

from typing import Any

from disclosure_alpha.edgar.types import FilingNotFoundError, SecFetchError
from disclosure_alpha.pipeline import extract_sections_from_html, load_filing_bundle
from disclosure_alpha.validation.matrix_corpus import sections_for_form

ITEM_1A = "item_1a_risk_factors"


def build_item1a_row(
    ticker: str,
    fiscal_year: int,
    *,
    form_type: str = "10-K",
    min_confidence: float = 0.75,
    min_word_count: int = 200,
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        bundle = load_filing_bundle(
            ticker,
            fiscal_year,
            form_type=form_type,
            use_cache=True,
            compare_prior=False,
        )
        sections = extract_sections_from_html(
            bundle.html,
            bundle.ref.form_type,
            cik=bundle.ref.cik,
            accession_number=bundle.ref.accession_number,
        )
        sec = next((s for s in sections if s.section_name == ITEM_1A), None)
        if sec is None:
            return None, "no_item_1a"
        tier = (
            "analysis"
            if sec.word_count >= min_word_count and sec.extraction_confidence >= min_confidence
            else "extracted"
        )
        return {
            "ticker": ticker,
            "fiscal_year": bundle.ref.fiscal_year,
            "filing_date": bundle.ref.filing_date,
            "section_name": sec.section_name,
            "cleaned_text": sec.cleaned_text,
            "word_count": sec.word_count,
            "extraction_confidence": sec.extraction_confidence,
            "extraction_method": sec.extraction_method,
            "warnings": sec.warnings,
            "quality_tier": tier,
            "accession_number": bundle.ref.accession_number,
            "cik": bundle.ref.cik,
        }, None
    except FilingNotFoundError:
        return None, "filing_not_found"
    except SecFetchError:
        return None, "sec_fetch_error"
    except ValueError:
        return None, "value_error"


def build_matrix_row(
    ticker: str,
    fiscal_year: int,
    *,
    form_type: str = "10-K",
    compare_prior: bool = True,
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        bundle = load_filing_bundle(
            ticker,
            fiscal_year,
            form_type=form_type,
            use_cache=True,
            compare_prior=compare_prior,
        )
        required = sections_for_form(form_type)
        sections = extract_sections_from_html(
            bundle.html,
            form_type,
            cik=bundle.ref.cik,
            accession_number=bundle.ref.accession_number,
        )
        section_map = {
            s.section_name: s.cleaned_text
            for s in sections
            if s.section_name in required and s.cleaned_text
        }
        if not section_map:
            return None, "no_matrix_sections"
        prior_map: dict[str, str] = {}
        if bundle.prior_html:
            prior_sections = extract_sections_from_html(
                bundle.prior_html,
                form_type,
                cik=bundle.ref.cik,
                accession_number=bundle.prior_accession or "prior",
            )
            prior_map = {
                s.section_name: s.cleaned_text
                for s in prior_sections
                if s.section_name in required and s.cleaned_text
            }
        quality: dict[str, dict[str, Any]] = {}
        for s in sections:
            if s.section_name in section_map:
                quality[s.section_name] = {
                    "word_count": s.word_count,
                    "extraction_confidence": s.extraction_confidence,
                    "warnings": list(s.warnings or []),
                    "extraction_method": getattr(s, "extraction_method", None),
                }
        return {
            "ticker": ticker,
            "fiscal_year": bundle.ref.fiscal_year,
            "form_type": form_type,
            "sections": section_map,
            "prior_sections": prior_map,
            "quality": quality,
            "accession_number": bundle.ref.accession_number,
            "cik": bundle.ref.cik,
        }, None
    except FilingNotFoundError:
        return None, "filing_not_found"
    except SecFetchError:
        return None, "sec_fetch_error"
    except ValueError:
        return None, "value_error"
