"""In-process metrics cache tests."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from disclosure_alpha.cache import TTLCache, metrics_cache, metrics_cache_key
from disclosure_alpha.pipeline import FilingMetricsResult, metrics_filing_ticker, score_filing_html
from html_fixtures import minimal_10k_html


def _sample_result(ticker: str = "AAPL") -> FilingMetricsResult:
    scored = score_filing_html(minimal_10k_html(), "10-K", cik="1", accession_number="t")
    return FilingMetricsResult(
        metrics=scored.metrics,
        filing={"ticker": ticker, "fiscal_year": 2025, "form_type": "10-K"},
        versions={},
    )


@pytest.fixture(autouse=True)
def _clear_metrics_cache(monkeypatch):
    monkeypatch.delenv("METRICS_CACHE_TTL_SECONDS", raising=False)
    monkeypatch.delenv("METRICS_CACHE_MAX_SIZE", raising=False)
    import disclosure_alpha.cache as cache_mod

    cache_mod._metrics_cache = None
    yield
    cache_mod._metrics_cache = None


def test_ttl_cache_hit_miss():
    cache = TTLCache(ttl_seconds=60, max_size=8)
    cache.set(("A",), "one")
    assert cache.get(("A",)) == "one"
    assert cache.get(("B",)) is None


def test_ttl_cache_expiry(monkeypatch):
    cache = TTLCache(ttl_seconds=1, max_size=8)
    times = [100.0, 100.0, 102.0]
    monkeypatch.setattr("disclosure_alpha.cache.time.monotonic", lambda: times.pop(0))
    cache.set(("k",), "v")
    assert cache.get(("k",)) == "v"
    assert cache.get(("k",)) is None


def test_ttl_cache_fifo_eviction():
    cache = TTLCache(ttl_seconds=60, max_size=2)
    cache.set(("a",), 1)
    cache.set(("b",), 2)
    cache.set(("c",), 3)
    assert cache.get(("a",)) is None
    assert cache.get(("b",)) == 2
    assert cache.get(("c",)) == 3


@patch("disclosure_alpha.pipeline._metrics_filing_ticker_uncached")
def test_metrics_filing_ticker_cache_hit(mock_uncached):
    mock_uncached.return_value = _sample_result()
    metrics_filing_ticker("AAPL", 2025, form_type="10-K", compare_prior=True)
    metrics_filing_ticker("AAPL", 2025, form_type="10-K", compare_prior=True)
    assert mock_uncached.call_count == 1


@patch("disclosure_alpha.pipeline._metrics_filing_ticker_uncached")
def test_metrics_filing_ticker_compare_prior_separate_entries(mock_uncached):
    mock_uncached.side_effect = [_sample_result(), _sample_result("AAPL")]
    metrics_filing_ticker("AAPL", 2025, compare_prior=True)
    metrics_filing_ticker("AAPL", 2025, compare_prior=False)
    assert mock_uncached.call_count == 2


@patch("disclosure_alpha.pipeline._metrics_filing_ticker_uncached")
def test_metrics_filing_ticker_cache_disabled(mock_uncached, monkeypatch):
    monkeypatch.setenv("METRICS_CACHE_TTL_SECONDS", "0")
    import disclosure_alpha.cache as cache_mod

    cache_mod._metrics_cache = None
    mock_uncached.return_value = _sample_result()
    metrics_filing_ticker("AAPL", 2025)
    metrics_filing_ticker("AAPL", 2025)
    assert mock_uncached.call_count == 2


@patch("disclosure_alpha.pipeline._metrics_filing_ticker_uncached")
def test_metrics_filing_ticker_does_not_cache_errors(mock_uncached):
    mock_uncached.side_effect = [ValueError("bad"), _sample_result()]
    with pytest.raises(ValueError, match="bad"):
        metrics_filing_ticker("BAD", 2025)
    metrics_filing_ticker("BAD", 2025)
    assert mock_uncached.call_count == 2


def test_metrics_cache_key_normalizes_ticker():
    assert metrics_cache_key("aapl", 2025, "10-K", None, True) == (
        "AAPL",
        2025,
        "10-K",
        None,
        True,
    )


def test_metrics_cache_disabled_when_ttl_zero(monkeypatch):
    monkeypatch.setenv("METRICS_CACHE_TTL_SECONDS", "0")
    import disclosure_alpha.cache as cache_mod

    cache_mod._metrics_cache = None
    assert metrics_cache().enabled is False
