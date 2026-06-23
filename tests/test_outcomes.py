"""Tests for L3 outcome helpers."""

from __future__ import annotations

import os
import sys
from datetime import date

import pytest

from disclosure_alpha.validation.outcomes import (
    earnings_rows_from_yfinance,
    fetch_realized_vol_90d_yfinance,
    first_reported_earnings_after,
    realized_vol_90d_from_bars,
)


def test_realized_vol_90d_from_flat_bars_is_low():
    filing = date(2025, 1, 1)
    bars = [
        {"date": f"2025-01-{d:02d}", "close": 100.0}
        for d in range(2, 32)
    ]
    vol, n = realized_vol_90d_from_bars(bars, filing_date=filing)
    assert n >= 20
    assert vol == 0.0


def test_realized_vol_90d_from_noisy_bars_is_positive():
    filing = date(2025, 1, 1)
    bars = []
    price = 100.0
    cur = date(2025, 1, 2)
    end = date(2025, 4, 1)
    i = 0
    while cur <= end:
        # alternating shocks -> non-zero realized vol
        shock = 0.01 if i % 2 == 0 else -0.008
        price *= 1.0 + shock
        bars.append({"date": cur.isoformat(), "close": price})
        cur = cur.fromordinal(cur.toordinal() + 1)
        i += 1

    vol, n = realized_vol_90d_from_bars(bars, filing_date=filing)
    assert n >= 20
    assert vol is not None
    assert vol > 0.05


def test_first_reported_earnings_after_picks_earliest():
    rows = [
        {
            "earnings_date": "2025-12-01",
            "reported_eps": 1.0,
            "estimate_eps": 0.9,
            "surprise_abs": 0.1,
        },
        {
            "earnings_date": "2025-05-01",
            "reported_eps": 1.2,
            "estimate_eps": 1.0,
            "surprise_abs": 0.2,
        },
    ]
    match = first_reported_earnings_after(rows, date(2025, 1, 15))
    assert match is not None
    assert match["earnings_date"].startswith("2025-05")


def test_fetch_realized_vol_90d_yfinance_from_history(monkeypatch):
    class _FakeFrame:
        empty = False

        def iterrows(self):
            price = 100.0
            cur = date(2025, 1, 2)
            end = date(2025, 4, 1)
            i = 0
            while cur <= end:
                shock = 0.01 if i % 2 == 0 else -0.008
                price *= 1.0 + shock
                yield cur, {"Close": price}
                cur = cur.fromordinal(cur.toordinal() + 1)
                i += 1

    class _FakeTicker:
        def __init__(self, _symbol: str):
            pass

        def history(self, **_kwargs):
            return _FakeFrame()

    class _FakeYF:
        Ticker = _FakeTicker

    monkeypatch.setitem(sys.modules, "yfinance", _FakeYF())
    vol, n, err = fetch_realized_vol_90d_yfinance("AAPL", date(2025, 1, 1))
    assert err is None
    assert n >= 20
    assert vol is not None
    assert vol > 0.05


@pytest.mark.integration
def test_earnings_rows_from_yfinance_aapl():
    if not os.environ.get("RUN_INTEGRATION"):
        pytest.skip("Set RUN_INTEGRATION=1 to run live yfinance tests")
    try:
        import yfinance  # noqa: F401
    except ImportError:
        pytest.skip("yfinance not installed")
    try:
        rows = earnings_rows_from_yfinance("AAPL", limit=8)
    except Exception as exc:
        pytest.skip(f"yfinance network unavailable: {exc}")
    assert rows
    assert "surprise_abs" in rows[0]
