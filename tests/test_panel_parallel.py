"""Panel screener parallelism and cache reuse."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from disclosure_alpha.edgar.types import EdgarError
from disclosure_alpha.pipeline import (
    FilingMetricsResult,
    PanelBatchResult,
    score_filing_html,
    score_panel_tickers,
)
from html_fixtures import minimal_10k_html


def _metrics_result(ticker: str) -> FilingMetricsResult:
    scored = score_filing_html(minimal_10k_html(), "10-K", cik="1", accession_number="t")
    return FilingMetricsResult(
        metrics=scored.metrics,
        filing={"ticker": ticker, "fiscal_year": 2025, "form_type": "10-K"},
        versions={},
    )


@patch("disclosure_alpha.pipeline.metrics_filing_ticker")
def test_panel_preserves_ticker_order(mock_metrics):
    mock_metrics.side_effect = lambda t, *a, **k: _metrics_result(t)
    batch = score_panel_tickers(["ZZZ", "AAA", "MMM"], 2025, max_workers=3)
    assert [r.ticker for r in batch.results] == ["ZZZ", "AAA", "MMM"]
    assert batch.summary["ok"] == 3


@patch("disclosure_alpha.pipeline.metrics_filing_ticker")
def test_panel_per_ticker_error_isolation(mock_metrics):
    def _fetch(ticker, *args, **kwargs):
        if ticker == "BAD":
            raise EdgarError("no filing")
        return _metrics_result(ticker)

    mock_metrics.side_effect = _fetch
    batch = score_panel_tickers(["AAPL", "BAD", "MSFT"], 2025, max_workers=3)
    assert batch.summary == {"ok": 2, "failed": 1}
    by_ticker = {r.ticker: r for r in batch.results}
    assert by_ticker["BAD"].status == "error"
    assert by_ticker["AAPL"].status == "ok"


@patch("disclosure_alpha.pipeline._score_panel_ticker")
def test_panel_uses_thread_pool_when_workers_gt_one(mock_score):
    from concurrent.futures import Future

    from disclosure_alpha.pipeline import PanelTickerResult

    mock_score.side_effect = lambda raw, *a, **k: PanelTickerResult(
        ticker=raw.strip().upper(),
        status="ok",
    )
    with patch("disclosure_alpha.pipeline.ThreadPoolExecutor") as mock_pool_cls:
        pool = mock_pool_cls.return_value.__enter__.return_value

        def _submit(fn, *args, **kwargs):
            fut = Future()
            fut.set_result(fn(*args, **kwargs))
            return fut

        pool.submit.side_effect = _submit
        score_panel_tickers(["A", "B"], 2025, max_workers=2)
    mock_pool_cls.assert_called_once_with(max_workers=2)


@patch("disclosure_alpha.pipeline._metrics_filing_ticker_uncached")
def test_panel_reuses_metrics_cache(mock_uncached):
    import disclosure_alpha.cache as cache_mod

    cache_mod._metrics_cache = None
    mock_uncached.return_value = _metrics_result("AAPL")
    score_panel_tickers(["AAPL", "AAPL"], 2025, max_workers=1)
    assert mock_uncached.call_count == 1
