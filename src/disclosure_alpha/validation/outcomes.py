"""L3 outcome helpers: post-filing vol and next-quarter earnings surprise."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from typing import Any, Literal

from disclosure_alpha.validation.openbb_client import OpenBBClient, OpenBBError

OutcomeSource = Literal["openbb:yfinance", "yfinance", "missing"]


@dataclass
class OutcomeRow:
    ticker: str
    fiscal_year: int | None
    filing_date: str | None
    realized_vol_90d: float | None = None
    vol_trading_days: int | None = None
    vol_source: OutcomeSource = "missing"
    next_earnings_date: str | None = None
    earnings_surprise_abs: float | None = None
    earnings_eps_estimate: float | None = None
    earnings_eps_reported: float | None = None
    earnings_source: OutcomeSource = "missing"
    errors: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        if out["errors"] is None:
            out["errors"] = []
        return out


def parse_iso_date(value: str | date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def realized_vol_annualized(daily_returns: list[float]) -> float | None:
    clean = [r for r in daily_returns if math.isfinite(r)]
    if len(clean) < 20:
        return None
    mean = sum(clean) / len(clean)
    var = sum((r - mean) ** 2 for r in clean) / (len(clean) - 1)
    if var <= 0:
        return 0.0
    return math.sqrt(var) * math.sqrt(252)


def realized_vol_90d_from_bars(
    bars: list[dict[str, Any]],
    *,
    filing_date: date,
    window_days: int = 90,
) -> tuple[float | None, int]:
    """Compute annualized realized vol over calendar days (filing_date+1 .. +window_days)."""
    start = filing_date + timedelta(days=1)
    end = filing_date + timedelta(days=window_days)
    points: list[tuple[date, float]] = []
    for bar in bars:
        d = parse_iso_date(bar["date"])
        close = bar.get("close")
        if close is None or not math.isfinite(float(close)):
            continue
        if start <= d <= end:
            points.append((d, float(close)))
    points.sort(key=lambda x: x[0])
    if len(points) < 2:
        return None, len(points)

    returns: list[float] = []
    for i in range(1, len(points)):
        prev = points[i - 1][1]
        cur = points[i][1]
        if prev <= 0:
            continue
        returns.append(math.log(cur / prev))

    vol = realized_vol_annualized(returns)
    return vol, len(returns)


def fetch_realized_vol_90d_openbb(
    client: OpenBBClient,
    ticker: str,
    filing_date: date,
    *,
    window_days: int = 90,
    provider: str = "yfinance",
) -> tuple[float | None, int, str | None]:
    start = (filing_date + timedelta(days=1)).isoformat()
    end = (filing_date + timedelta(days=window_days + 5)).isoformat()
    try:
        bars = client.equity_price_historical(
            ticker, start_date=start, end_date=end, provider=provider
        )
    except OpenBBError as exc:
        return None, 0, str(exc)
    vol, n = realized_vol_90d_from_bars(bars, filing_date=filing_date, window_days=window_days)
    return vol, n, None


def fetch_realized_vol_90d_yfinance(
    ticker: str,
    filing_date: date,
    *,
    window_days: int = 90,
) -> tuple[float | None, int, str | None]:
    import yfinance as yf

    start = (filing_date + timedelta(days=1)).isoformat()
    end = (filing_date + timedelta(days=window_days + 5)).isoformat()
    try:
        frame = yf.Ticker(ticker).history(start=start, end=end, auto_adjust=False)
    except Exception as exc:  # ponytail: yfinance errors are heterogeneous
        return None, 0, str(exc)
    if frame is None or frame.empty:
        return None, 0, None
    bars: list[dict[str, Any]] = []
    for idx, rec in frame.iterrows():
        close = rec.get("Close")
        if close is None:
            continue
        bars.append(
            {
                "date": idx.isoformat() if hasattr(idx, "isoformat") else str(idx),
                "close": float(close),
            }
        )
    vol, n = realized_vol_90d_from_bars(bars, filing_date=filing_date, window_days=window_days)
    return vol, n, None


def first_reported_earnings_after(
    earnings_rows: list[dict[str, Any]],
    after: date,
) -> dict[str, Any] | None:
    """Pick earliest reported earnings strictly after ``after``."""
    candidates: list[tuple[date, dict[str, Any]]] = []
    for row in earnings_rows:
        ed = row.get("earnings_date")
        reported = row.get("reported_eps")
        estimate = row.get("estimate_eps")
        if ed is None or reported is None or estimate is None:
            continue
        d = parse_iso_date(ed)
        if d <= after:
            continue
        candidates.append((d, row))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def earnings_rows_from_yfinance(ticker: str, *, limit: int = 24) -> list[dict[str, Any]]:
    import yfinance as yf

    frame = yf.Ticker(ticker).get_earnings_dates(limit=limit)
    if frame is None or frame.empty:
        return []

    rows: list[dict[str, Any]] = []
    for idx, row in frame.iterrows():
        reported = row.get("Reported EPS")
        estimate = row.get("EPS Estimate")
        if reported is None or estimate is None:
            continue
        try:
            reported_f = float(reported)
            estimate_f = float(estimate)
        except (TypeError, ValueError):
            continue
        if math.isnan(reported_f) or math.isnan(estimate_f):
            continue
        rows.append(
            {
                "earnings_date": idx.isoformat() if hasattr(idx, "isoformat") else str(idx),
                "reported_eps": reported_f,
                "estimate_eps": estimate_f,
                "surprise_abs": abs(reported_f - estimate_f),
            }
        )
    return rows


def fetch_next_earnings_surprise_yfinance(
    ticker: str,
    filing_date: date,
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        rows = earnings_rows_from_yfinance(ticker)
    except Exception as exc:  # ponytail: yfinance errors are heterogeneous
        return None, str(exc)
    match = first_reported_earnings_after(rows, filing_date)
    return match, None


def resolve_filing_date_edgar(
    ticker: str,
    fiscal_year: int,
    *,
    form_type: str = "10-K",
    use_cache: bool = True,
) -> str | None:
    from disclosure_alpha.edgar.resolver import resolve_filing

    ref = resolve_filing(ticker, fiscal_year, form_type, use_cache=use_cache)
    return ref.filing_date


def fetch_outcomes_for_filing(
    *,
    ticker: str,
    fiscal_year: int | None,
    filing_date: str | date | None,
    openbb: OpenBBClient | None = None,
    fetch_vol: bool = True,
    fetch_earnings: bool = True,
    resolve_filing_from_edgar: bool = True,
    vol_provider: Literal["openbb", "yfinance"] = "openbb",
) -> OutcomeRow:
    errors: list[str] = []
    row = OutcomeRow(ticker=ticker.upper(), fiscal_year=fiscal_year, filing_date=None, errors=[])

    fdate: date | None = None
    if filing_date is not None:
        fdate = parse_iso_date(filing_date)
        row.filing_date = fdate.isoformat()
    elif resolve_filing_from_edgar and fiscal_year is not None:
        try:
            resolved = resolve_filing_date_edgar(ticker, fiscal_year)
            if resolved:
                fdate = parse_iso_date(resolved)
                row.filing_date = fdate.isoformat()
        except Exception as exc:
            errors.append(f"filing_date: {exc}")

    if fdate is None:
        errors.append("missing filing_date")
        row.errors = errors
        return row

    if fetch_vol:
        if vol_provider == "openbb":
            if openbb is None:
                errors.append("vol: OpenBB client not configured")
            else:
                vol, n, err = fetch_realized_vol_90d_openbb(openbb, ticker, fdate)
                if err:
                    errors.append(f"vol: {err}")
                else:
                    row.realized_vol_90d = vol
                    row.vol_trading_days = n
                    row.vol_source = "openbb:yfinance" if vol is not None else "missing"
        else:
            vol, n, err = fetch_realized_vol_90d_yfinance(ticker, fdate)
            if err:
                errors.append(f"vol: {err}")
            else:
                row.realized_vol_90d = vol
                row.vol_trading_days = n
                row.vol_source = "yfinance" if vol is not None else "missing"

    if fetch_earnings:
        match, err = fetch_next_earnings_surprise_yfinance(ticker, fdate)
        if err:
            errors.append(f"earnings: {err}")
        elif match is None:
            errors.append("earnings: no reported quarter after filing_date")
        else:
            row.next_earnings_date = parse_iso_date(match["earnings_date"]).isoformat()
            row.earnings_eps_estimate = match["estimate_eps"]
            row.earnings_eps_reported = match["reported_eps"]
            row.earnings_surprise_abs = match["surprise_abs"]
            row.earnings_source = "yfinance"

    row.errors = errors
    return row
