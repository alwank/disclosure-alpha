from __future__ import annotations

import re
from dataclasses import replace
from typing import Any

from disclosure_alpha.edgar import cache, client
from disclosure_alpha.edgar.types import FilingNotFoundError, FilingRef, SecFetchError

_QUARTERS = ("Q1", "Q2", "Q3")
_FORM_BASE = {"10-K": "10-K", "10-Q": "10-Q"}
_FY_RE = re.compile(
    r'name="dei:DocumentFiscalYearFocus"[^>]*>(\d{4})<',
    re.IGNORECASE,
)
_PERIOD_RE = re.compile(
    r'name="dei:DocumentFiscalPeriodFocus"[^>]*>([^<]+)<',
    re.IGNORECASE,
)


def normalize_form_type(form_type: str) -> str:
    base = form_type.upper().replace("/A", "").replace("-A", "").strip()
    if base not in _FORM_BASE:
        raise ValueError(f"Unsupported form_type: {form_type}")
    return base


def _try_normalize_form_type(form_type: str) -> str | None:
    try:
        return normalize_form_type(form_type)
    except ValueError:
        return None


def normalize_quarter(quarter: str | None) -> str | None:
    if quarter is None:
        return None
    q = quarter.upper().strip()
    if q not in _QUARTERS:
        raise ValueError(f"quarter must be one of {_QUARTERS}")
    return q


def parse_fiscal_tags(html: str) -> tuple[int | None, str | None]:
    fy_match = _FY_RE.search(html)
    period_match = _PERIOD_RE.search(html)
    fiscal_year = int(fy_match.group(1)) if fy_match else None
    period = period_match.group(1).strip().upper() if period_match else None
    return fiscal_year, period


def _is_amendment(form: str) -> bool:
    return form.upper().endswith("/A") or form.upper().endswith("-A")


def _flatten_recent(recent: dict[str, Any]) -> list[dict[str, str]]:
    keys = ("accessionNumber", "form", "filingDate", "reportDate", "primaryDocument")
    n = len(recent.get("form", []))
    rows: list[dict[str, str]] = []
    for i in range(n):
        rows.append({k: str(recent.get(k, [""] * n)[i]) for k in keys})
    return rows


def _iter_submissions(submissions: dict[str, Any]) -> list[dict[str, str]]:
    rows = _flatten_recent(submissions.get("filings", {}).get("recent", {}))
    for file_meta in submissions.get("filings", {}).get("files", []):
        name = file_meta.get("name")
        if not name:
            continue
        try:
            blob = client.fetch_json(f"{client.DATA_BASE}/submissions/{name}")
            if "filings" in blob:
                rows.extend(_flatten_recent(blob.get("filings", {}).get("recent", {})))
            else:
                rows.extend(_flatten_recent(blob))
        except SecFetchError:
            continue
    return rows


def _period_matches(form_type: str, period: str | None, quarter: str | None) -> bool:
    if form_type == "10-K":
        return period in (None, "FY", "")
    return period == quarter


def _candidate_score(
    row: dict[str, str],
    *,
    form_type: str,
    fiscal_year: int,
    quarter: str | None,
    fiscal_year_html: int | None,
    period_html: str | None,
) -> int | None:
    form = row["form"]
    base = _try_normalize_form_type(form)
    if base is None or base != form_type:
        return None

    fy = fiscal_year_html
    period = period_html
    if fy is None and row.get("reportDate"):
        try:
            fy = int(row["reportDate"][:4])
        except ValueError:
            fy = None
    if fy != fiscal_year:
        return None
    if not _period_matches(form_type, period, quarter):
        return None
    # Prefer non-amendment; tie-break by later filing_date
    score = 0 if _is_amendment(form) else 100
    score += int(row.get("filingDate", "0000-00-00").replace("-", ""))
    return score


def resolve_cik(ticker: str, *, tickers: dict[str, tuple[str, str]] | None = None) -> str:
    mapping = tickers or client.fetch_company_tickers()
    key = ticker.upper().strip()
    if key not in mapping:
        raise FilingNotFoundError(f"Unknown ticker: {ticker}")
    return mapping[key][0]


def list_filings(
    ticker: str,
    fiscal_year: int,
    *,
    form_type: str | None = None,
    use_cache: bool = True,
    cache_dir=None,
) -> list[FilingRef]:
    cache_dir = cache_dir or cache.default_cache_dir()
    cik = resolve_cik(ticker)
    submissions = client.fetch_submissions(cik)
    rows = _iter_submissions(submissions)
    forms = {normalize_form_type(form_type)} if form_type else {"10-K", "10-Q"}
    best: dict[tuple[str, str | None], tuple[int, FilingRef]] = {}

    for row in rows:
        base = _try_normalize_form_type(row["form"])
        if base is None or base not in forms:
            continue
        if row.get("reportDate"):
            try:
                if int(row["reportDate"][:4]) != fiscal_year:
                    continue
            except ValueError:
                pass

        html = cache.read_cached_html(cache_dir, cik, row["accessionNumber"]) if use_cache else None
        if html is None:
            try:
                url = client.filing_document_url(cik, row["accessionNumber"], row["primaryDocument"])
                html = client.fetch_text(url)
            except SecFetchError:
                continue

        fy_html, period_html = parse_fiscal_tags(html)
        if fy_html != fiscal_year:
            continue
        if base == "10-K":
            if period_html in _QUARTERS:
                continue
            quarter_val = None
        else:
            if period_html not in _QUARTERS:
                continue
            quarter_val = period_html

        ref = FilingRef(
            cik=cik,
            ticker=ticker.upper(),
            accession_number=row["accessionNumber"],
            form_type=base,
            fiscal_year=fiscal_year,
            quarter=quarter_val,
            filing_date=row["filingDate"],
            report_date=row.get("reportDate") or None,
            primary_document=row["primaryDocument"],
            html_path=cache.html_path(cache_dir, cik, row["accessionNumber"]),
        )
        if use_cache:
            cache.write_cache(cache_dir, ref, html)

        key = (base, quarter_val)
        score = 0 if _is_amendment(row["form"]) else 100
        score += int(row.get("filingDate", "0000-00-00").replace("-", ""))
        prev = best.get(key)
        if prev is None or score > prev[0]:
            best[key] = (score, ref)

    return sorted((v[1] for v in best.values()), key=lambda r: (r.form_type, r.quarter or ""))


def resolve_filing(
    ticker: str,
    fiscal_year: int,
    form_type: str = "10-K",
    quarter: str | None = None,
    *,
    use_cache: bool = True,
    cache_dir=None,
) -> FilingRef:
    base = normalize_form_type(form_type)
    q = normalize_quarter(quarter)
    if base == "10-Q" and q is None:
        raise ValueError("quarter is required for 10-Q (Q1, Q2, or Q3)")

    cache_dir = cache_dir or cache.default_cache_dir()
    cik = resolve_cik(ticker)
    submissions = client.fetch_submissions(cik)
    rows = _iter_submissions(submissions)

    best_row: dict[str, str] | None = None
    best_score = -1
    best_html: str | None = None

    for row in rows:
        html = None
        if use_cache:
            html = cache.read_cached_html(cache_dir, cik, row["accessionNumber"])
        fy_html, period_html = (None, None)
        if html:
            fy_html, period_html = parse_fiscal_tags(html)
        score = _candidate_score(
            row,
            form_type=base,
            fiscal_year=fiscal_year,
            quarter=q,
            fiscal_year_html=fy_html,
            period_html=period_html,
        )
        if score is None:
            continue
        if html is None:
            try:
                url = client.filing_document_url(cik, row["accessionNumber"], row["primaryDocument"])
                html = client.fetch_text(url)
                fy_html, period_html = parse_fiscal_tags(html)
                score = _candidate_score(
                    row,
                    form_type=base,
                    fiscal_year=fiscal_year,
                    quarter=q,
                    fiscal_year_html=fy_html,
                    period_html=period_html,
                )
                if score is None:
                    continue
            except SecFetchError:
                continue
        if score > best_score:
            best_score = score
            best_row = row
            best_html = html

    if best_row is None or best_html is None:
        label = f"{ticker} FY{fiscal_year} {base}"
        if q:
            label += f" {q}"
        raise FilingNotFoundError(f"No filing found for {label}")

    _, period_html = parse_fiscal_tags(best_html)
    ref = FilingRef(
        cik=cik,
        ticker=ticker.upper(),
        accession_number=best_row["accessionNumber"],
        form_type=base,
        fiscal_year=fiscal_year,
        quarter=q if base == "10-Q" else None,
        filing_date=best_row["filingDate"],
        report_date=best_row.get("reportDate") or None,
        primary_document=best_row["primaryDocument"],
    )
    if use_cache:
        path = cache.write_cache(cache_dir, ref, best_html)
        ref = replace(ref, html_path=path)
    return ref


def resolve_prior_filing(ref: FilingRef, *, use_cache: bool = True, cache_dir=None) -> FilingRef | None:
    if ref.form_type == "10-K":
        return resolve_filing(
            ref.ticker,
            ref.fiscal_year - 1,
            "10-K",
            use_cache=use_cache,
            cache_dir=cache_dir,
        )
    if ref.form_type == "10-Q" and ref.quarter:
        order = list(_QUARTERS)
        idx = order.index(ref.quarter)
        if idx == 0:
            return resolve_filing(
                ref.ticker,
                ref.fiscal_year - 1,
                "10-Q",
                quarter="Q3",
                use_cache=use_cache,
                cache_dir=cache_dir,
            )
        return resolve_filing(
            ref.ticker,
            ref.fiscal_year,
            "10-Q",
            quarter=order[idx - 1],
            use_cache=use_cache,
            cache_dir=cache_dir,
        )
    return None


def load_filing_html(ref: FilingRef, *, use_cache: bool = True, cache_dir=None) -> str:
    cache_dir = cache_dir or cache.default_cache_dir()
    if use_cache:
        cached = cache.read_cached_html(cache_dir, ref.cik, ref.accession_number)
        if cached:
            return cached
    url = client.filing_document_url(ref.cik, ref.accession_number, ref.primary_document)
    html = client.fetch_text(url)
    if use_cache:
        cache.write_cache(cache_dir, ref, html)
    return html
