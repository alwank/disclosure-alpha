"""Exact filing evidence and combined review endpoint."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from disclosure_alpha.api.routes import app
from disclosure_alpha.edgar.types import FilingNotFoundError, SecFetchError
from disclosure_alpha.pipeline import FilingMetricsResult, score_filing_html
from disclosure_alpha.text_metrics import detect_section_flags, detect_section_flags_with_evidence
from html_fixtures import minimal_10k_html, minimal_prior_html

client = TestClient(app)


def _result(*, with_prior: bool = False) -> FilingMetricsResult:
    scored = score_filing_html(
        minimal_10k_html(),
        "10-K",
        prior_html=minimal_prior_html() if with_prior else None,
        fiscal_year=2025,
    )
    return FilingMetricsResult(
        metrics=scored.metrics,
        sections=scored.sections,
        filing={
            "ticker": "AAPL",
            "cik": "0000320193",
            "accession_number": "0000320193-25-000079",
            "form_type": "10-K",
            "fiscal_year": 2025,
            "quarter": None,
            "filing_date": "2025-10-31",
            "report_date": "2025-09-27",
            "prior_accession_number": "0000320193-24-000077" if with_prior else None,
            "source_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl.htm",
        },
        versions=scored.versions,
    )


def test_flag_evidence_exact_offsets_repeated_overlap_and_unicode():
    text = (
        "😀 We identified a material weakness in internal control over financial reporting. "
        "A second material weakness exists."
    )
    flags, evidence = detect_section_flags_with_evidence(text, "item_9a_controls")
    hits = [item for item in evidence if item["flag"] == "material_weakness_flag"]
    assert flags["material_weakness_flag"] is True
    assert len(hits) == 2
    assert hits[0]["pattern"] == "material weakness in internal control over financial reporting"
    assert [text[item["start"]:item["end"]] for item in hits] == [
        item["matched_text"] for item in hits
    ]
    assert detect_section_flags(text, "item_9a_controls") == flags


def test_suppressed_and_out_of_scope_phrases_have_no_highlights():
    text = "No material weaknesses were identified. A material weakness could occur later."
    flags, evidence = detect_section_flags_with_evidence(text, "item_9a_controls")
    hits = [item for item in evidence if item["flag"] == "material_weakness_flag"]
    assert flags["material_weakness_flag"] is True
    assert len(hits) == 1
    assert hits[0]["matched_text"] == "material weakness"
    out_flags, out_evidence = detect_section_flags_with_evidence(text, "item_7_mdna")
    assert out_flags["material_weakness_flag"] is False
    assert not any(item["flag"] == "material_weakness_flag" for item in out_evidence)


@patch("disclosure_alpha.api.endpoints.review.metrics_filing_ticker")
@patch("disclosure_alpha.api.endpoints.matrix.metrics_filing_ticker")
def test_review_returns_same_score_and_exact_text_as_matrix(mock_matrix, mock_review):
    result = _result()
    mock_matrix.return_value = result
    mock_review.return_value = result
    params = {"fiscal_year": 2025, "form_type": "10-K"}
    review_response = client.get(
        "/v1/company/AAPL/filing-review",
        params=params,
        headers={"Accept-Encoding": "gzip"},
    )
    matrix_response = client.get("/v1/company/AAPL/disclosure-matrix", params=params)
    assert review_response.status_code == 200
    assert review_response.headers["content-encoding"] == "gzip"
    assert matrix_response.status_code == 200
    body = review_response.json()
    assert body["scores"] == matrix_response.json()["scores"]
    assert body["filing"]["source_url"].startswith("https://www.sec.gov/Archives/")
    assert mock_review.call_count == 1
    by_section = {section["section_name"]: section["cleaned_text"] for section in body["sections"]}
    for hit in body["evidence"]:
        assert by_section[hit["section"]][hit["start"]:hit["end"]] == hit["matched_text"]
        assert by_section[hit["section"]][hit["sentence_start"]:hit["sentence_end"]].strip() == hit["sentence"]
        assert (hit["section"], hit["flag"]) in {
            (item["section"], item["flag"]) for item in body["active_flags"]
        }
    for section in body["sections"]:
        text = section["cleaned_text"]
        assert " ".join(text[block["start"]:block["end"]] for block in section["reading_blocks"]) == text
    assert len(body["display"]["headline_rows"]) == 9
    assert body["changes"]["section_drivers"] == {}


@patch("disclosure_alpha.api.endpoints.review.metrics_filing_ticker")
def test_review_change_drivers_match_computed_section_diffs(mock_metrics):
    result = _result(with_prior=True)
    mock_metrics.return_value = result
    response = client.get(
        "/v1/company/AAPL/filing-review",
        params={"fiscal_year": 2025, "form_type": "10-K"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["filing"]["prior_accession_number"] == "0000320193-24-000077"
    drivers = body["changes"]["section_drivers"]
    assert drivers
    assert set(drivers) == set(body["changes"]["section_diffs"])
    for section, details in drivers.items():
        assert details["added_sentence_count"] >= 0
        assert details["removed_sentence_count"] >= 0
        assert details["changed_numeric_count"] >= 0
        assert isinstance(details["new_topics"], list)
        assert isinstance(details["intensified_topics"], list)
        assert details["language_deltas"] == body["changes"]["language_deltas"][section]
        assert 0 <= details["confidence_score"] <= 1


@patch("disclosure_alpha.api.endpoints.review.metrics_filing_ticker")
def test_review_compare_none_skips_prior(mock_metrics):
    mock_metrics.return_value = _result()
    response = client.get(
        "/v1/company/AAPL/filing-review",
        params={"fiscal_year": 2025, "compare": "none"},
    )
    assert response.status_code == 200
    assert response.json()["changes"]["change_score"]["missing_reason"] == "compare=none"
    assert response.json()["changes"]["section_drivers"] == {}
    assert mock_metrics.call_args.kwargs["compare_prior"] is False


def test_review_requires_10q_quarter():
    response = client.get(
        "/v1/company/AAPL/filing-review",
        params={"fiscal_year": 2025, "form_type": "10-Q"},
    )
    assert response.status_code == 422


@patch("disclosure_alpha.api.endpoints.review.metrics_filing_ticker")
def test_review_edgar_errors(mock_metrics):
    for error, status in (
        (FilingNotFoundError("missing"), 404),
        (SecFetchError("upstream unavailable"), 502),
    ):
        mock_metrics.side_effect = error
        response = client.get(
            "/v1/company/AAPL/filing-review", params={"fiscal_year": 2025}
        )
        assert response.status_code == status
