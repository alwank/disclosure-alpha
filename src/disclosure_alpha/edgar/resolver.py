from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from disclosure_alpha.edgar import cache, client
from disclosure_alpha.edgar.types import FilingNotFoundError, FilingRef, SecFetchError

_QUARTERS = ("Q1", "Q2", "Q3")
_FORM_BASE = {"10-K": "10-K", "10-Q": "10-Q"}
_MAX_DISAMBIGUATION = 3  # ponytail: cap HTML fetches per target when metadata ties
_FY_RE = re.compile(
    r'name="dei:DocumentFiscalYearFocus"[^>]*>(\d{4})<',
    re.IGNORECASE,
)
_PERIOD_RE = re.compile(
    r'name="dei:DocumentFiscalPeriodFocus"[^>]*>([^<]+)<',
    re.IGNORECASE,
)


@dataclass(frozen=True)
class FilingTarget:
    fiscal_year: int
    form_type: str
    quarter: str | None = None


@dataclass
class _TargetPick:
    best_score: int = -1
    best_row: dict[str, str] | None = None
    tied_rows: list[dict[str, str]] = field(default_factory=list)


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
    if not q:
        return None
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


def _load_submission_rows(ticker: str) -> tuple[str, list[dict[str, str]]]:
    cik = resolve_cik(ticker)
    submissions = client.fetch_submissions(cik)
    return cik, _iter_submissions(submissions)


def _period_matches(form_type: str, period: str | None, quarter: str | None) -> bool:
    if form_type == "10-K":
        return period in (None, "FY", "")
    return period == quarter


def _fiscal_year_match_tier(
    fiscal_year: int,
    *,
    fiscal_year_html: int | None,
    report_date: str | None,
    filing_date: str | None = None,
) -> int | None:
    """3=DEI exact, 2=reportDate year, 1=filingDate year, None=no match."""
    if fiscal_year_html == fiscal_year:
        return 3
    if report_date:
        try:
            if int(report_date[:4]) == fiscal_year:
                return 2
        except ValueError:
            pass
    if filing_date:
        try:
            if int(filing_date[:4]) == fiscal_year:
                return 1
        except ValueError:
            pass
    return None


def _fiscal_year_matches(
    fiscal_year: int,
    *,
    fiscal_year_html: int | None,
    report_date: str | None,
    filing_date: str | None = None,
) -> bool:
    return _fiscal_year_match_tier(
        fiscal_year,
        fiscal_year_html=fiscal_year_html,
        report_date=report_date,
        filing_date=filing_date,
    ) is not None


def _score_filing_row(
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

    tier = _fiscal_year_match_tier(
        fiscal_year,
        fiscal_year_html=fy,
        report_date=row.get("reportDate"),
        filing_date=row.get("filingDate"),
    )
    if tier is None:
        return None
    if not _period_matches(form_type, period, quarter):
        return None
    score = tier * 1_000_000_000
    score += 0 if _is_amendment(form) else 100_000
    score += int(row.get("filingDate", "0000-00-00").replace("-", ""))
    return score


def _candidate_score(
    row: dict[str, str],
    *,
    form_type: str,
    fiscal_year: int,
    quarter: str | None,
    fiscal_year_html: int | None,
    period_html: str | None,
) -> int | None:
    return _score_filing_row(
        row,
        form_type=form_type,
        fiscal_year=fiscal_year,
        quarter=quarter,
        fiscal_year_html=fiscal_year_html,
        period_html=period_html,
    )


def _weak_year_hint(row: dict[str, str], fiscal_year: int) -> bool:
    for field in ("reportDate", "filingDate"):
        val = row.get(field)
        if not val:
            continue
        try:
            if abs(int(val[:4]) - fiscal_year) <= 1:
                return True
        except ValueError:
            continue
    return False


def _candidate_year_distance(row: dict[str, str], fiscal_year: int) -> int:
    """Min |calendar year − target fiscal year| from report/filing dates."""
    best = 99
    for field in ("reportDate", "filingDate"):
        val = row.get(field)
        if not val:
            continue
        try:
            best = min(best, abs(int(val[:4]) - fiscal_year))
        except ValueError:
            continue
    return best


def _row_form_matches(row: dict[str, str], form_type: str) -> bool:
    return _try_normalize_form_type(row.get("form", "")) == form_type


def _html_dei_score(
    row: dict[str, str],
    html: str,
    *,
    form_type: str,
    fiscal_year: int,
    quarter: str | None,
) -> int | None:
    """Accept metadata mismatches when HTML DEI tags match requested fiscal year."""
    form = row["form"]
    base = _try_normalize_form_type(form)
    if base is None or base != form_type:
        return None
    fy_html, period_html = parse_fiscal_tags(html)
    if fy_html != fiscal_year:
        return None
    if not _period_matches(form_type, period_html, quarter):
        return None
    score = 500_000_000
    score += 0 if _is_amendment(form) else 100_000
    score += int(row.get("filingDate", "0000-00-00").replace("-", ""))
    return score


def _update_pick(pick: _TargetPick, row: dict[str, str], score: int) -> None:
    if score > pick.best_score:
        pick.best_score = score
        pick.best_row = row
        pick.tied_rows = [row]
    elif score == pick.best_score:
        if row not in pick.tied_rows:
            pick.tied_rows.append(row)


def _score_row_for_target(
    row: dict[str, str],
    target: FilingTarget,
    *,
    html: str | None,
) -> int | None:
    base = target.form_type
    fy_html, period_html = (None, None)
    if html:
        fy_html, period_html = parse_fiscal_tags(html)
        if base == "10-K" and period_html in _QUARTERS:
            return None

    score = _candidate_score(
        row,
        form_type=base,
        fiscal_year=target.fiscal_year,
        quarter=target.quarter,
        fiscal_year_html=fy_html,
        period_html=period_html,
    )
    if score is None and html:
        score = _html_dei_score(
            row,
            html,
            form_type=base,
            fiscal_year=target.fiscal_year,
            quarter=target.quarter,
        )
    return score


def _html_for_disambiguation(
    row: dict[str, str],
    cik: str,
    *,
    use_cache: bool,
    cache_dir,
) -> str | None:
    if use_cache:
        cached = cache.read_cached_html(cache_dir, cik, row["accessionNumber"])
        if cached:
            return cached
    try:
        url = client.filing_document_url(cik, row["accessionNumber"], row["primaryDocument"])
        return client.fetch_text_prefix(url)
    except SecFetchError:
        return None


def _disambiguate_target(
    target: FilingTarget,
    pick: _TargetPick,
    rows: list[dict[str, str]],
    *,
    cik: str,
    use_cache: bool,
    cache_dir,
) -> None:
    base = target.form_type
    candidates: list[dict[str, str]] = []
    if pick.best_score < 0:
        candidates = [
            row
            for row in rows
            if _row_form_matches(row, base) and _weak_year_hint(row, target.fiscal_year)
        ]
    elif len(pick.tied_rows) > 1:
        candidates = list(pick.tied_rows)

    if not candidates:
        return

    if pick.best_score < 0:
        # ponytail: cap HTML fetches; prefer rows whose dates sit near target FY
        candidates.sort(
            key=lambda r: (
                _candidate_year_distance(r, target.fiscal_year),
                r.get("reportDate", ""),
                r.get("filingDate", ""),
            )
        )

    best_score = pick.best_score
    best_row = pick.best_row
    for row in candidates[:_MAX_DISAMBIGUATION]:
        html = _html_for_disambiguation(row, cik, use_cache=use_cache, cache_dir=cache_dir)
        if not html:
            continue
        score = _score_row_for_target(row, target, html=html)
        if score is None:
            continue
        if score > best_score:
            best_score = score
            best_row = row

    if best_row is not None:
        pick.best_score = best_score
        pick.best_row = best_row


def _ref_from_row(
    row: dict[str, str],
    target: FilingTarget,
    *,
    cik: str,
    ticker: str,
    cache_dir,
    use_cache: bool,
) -> FilingRef:
    return FilingRef(
        cik=cik,
        ticker=ticker.upper(),
        accession_number=row["accessionNumber"],
        form_type=target.form_type,
        fiscal_year=target.fiscal_year,
        quarter=target.quarter if target.form_type == "10-Q" else None,
        filing_date=row["filingDate"],
        report_date=row.get("reportDate") or None,
        primary_document=row["primaryDocument"],
        html_path=cache.html_path(cache_dir, cik, row["accessionNumber"]) if use_cache else None,
    )


def _prior_filing_target(target: FilingTarget) -> FilingTarget | None:
    if target.form_type == "10-K":
        return FilingTarget(target.fiscal_year - 1, "10-K", None)
    if target.form_type == "10-Q" and target.quarter:
        order = list(_QUARTERS)
        idx = order.index(target.quarter)
        if idx == 0:
            return FilingTarget(target.fiscal_year - 1, "10-Q", "Q3")
        return FilingTarget(target.fiscal_year, "10-Q", order[idx - 1])
    return None


def _target_label(ticker: str, target: FilingTarget) -> str:
    label = f"{ticker} FY{target.fiscal_year} {target.form_type}"
    if target.quarter:
        label += f" {target.quarter}"
    return label


def resolve_filing_targets(
    ticker: str,
    targets: list[FilingTarget],
    *,
    use_cache: bool = True,
    cache_dir=None,
) -> dict[FilingTarget, FilingRef]:
    if not targets:
        return {}

    cache_dir = cache_dir or cache.default_cache_dir()
    normalized: list[FilingTarget] = []
    for target in targets:
        base = normalize_form_type(target.form_type)
        q = normalize_quarter(target.quarter)
        if base == "10-Q" and q is None:
            raise ValueError("quarter is required for 10-Q (Q1, Q2, or Q3)")
        normalized.append(FilingTarget(target.fiscal_year, base, q))

    cik, rows = _load_submission_rows(ticker)
    picks = {target: _TargetPick() for target in normalized}

    for row in rows:
        row_base = _try_normalize_form_type(row["form"])
        if row_base is None:
            continue
        html = cache.read_cached_html(cache_dir, cik, row["accessionNumber"]) if use_cache else None
        for target in normalized:
            if row_base != target.form_type:
                continue
            score = _score_row_for_target(row, target, html=html)
            if score is not None:
                _update_pick(picks[target], row, score)

    for target in normalized:
        _disambiguate_target(
            target,
            picks[target],
            rows,
            cik=cik,
            use_cache=use_cache,
            cache_dir=cache_dir,
        )

    out: dict[FilingTarget, FilingRef] = {}
    for target in normalized:
        pick = picks[target]
        if pick.best_row is None:
            raise FilingNotFoundError(f"No filing found for {_target_label(ticker, target)}")
        out[target] = _ref_from_row(
            pick.best_row,
            target,
            cik=cik,
            ticker=ticker,
            cache_dir=cache_dir,
            use_cache=use_cache,
        )
    return out


def resolve_filing_with_prior(
    ticker: str,
    fiscal_year: int,
    form_type: str = "10-K",
    quarter: str | None = None,
    *,
    compare_prior: bool = True,
    use_cache: bool = True,
    cache_dir=None,
) -> tuple[FilingRef, FilingRef | None]:
    base = normalize_form_type(form_type)
    q = normalize_quarter(quarter)
    if base == "10-Q" and q is None:
        raise ValueError("quarter is required for 10-Q (Q1, Q2, or Q3)")

    primary = FilingTarget(fiscal_year, base, q)
    targets = [primary]
    prior_target: FilingTarget | None = None
    if compare_prior:
        prior_target = _prior_filing_target(primary)
        if prior_target:
            targets.append(prior_target)

    resolved = resolve_filing_targets(
        ticker,
        targets,
        use_cache=use_cache,
        cache_dir=cache_dir,
    )
    prior_ref = resolved.get(prior_target) if prior_target else None
    return resolved[primary], prior_ref


def _ticker_lookup_keys(ticker: str) -> list[str]:
    key = ticker.upper().strip()
    keys = [key]
    if "-" in key:
        keys.append(key.replace("-", "."))
    if "." in key:
        keys.append(key.replace(".", "-"))
    return list(dict.fromkeys(keys))


def resolve_cik(ticker: str, *, tickers: dict[str, tuple[str, str]] | None = None) -> str:
    mapping = tickers or client.fetch_company_tickers()
    for key in _ticker_lookup_keys(ticker):
        if key in mapping:
            return mapping[key][0]
    raise FilingNotFoundError(f"Unknown ticker: {ticker}")


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

        html = cache.read_cached_html(cache_dir, cik, row["accessionNumber"]) if use_cache else None
        if html is None:
            try:
                url = client.filing_document_url(cik, row["accessionNumber"], row["primaryDocument"])
                html = client.fetch_text(url)
            except SecFetchError:
                continue

        fy_html, period_html = parse_fiscal_tags(html)
        if not _fiscal_year_matches(
            fiscal_year,
            fiscal_year_html=fy_html,
            report_date=row.get("reportDate"),
            filing_date=row.get("filingDate"),
        ):
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
    target = FilingTarget(fiscal_year, base, q)
    return resolve_filing_targets(
        ticker,
        [target],
        use_cache=use_cache,
        cache_dir=cache_dir,
    )[target]


def resolve_prior_filing(ref: FilingRef, *, use_cache: bool = True, cache_dir=None) -> FilingRef | None:
    prior_target = _prior_filing_target(
        FilingTarget(ref.fiscal_year, ref.form_type, ref.quarter)
    )
    if prior_target is None:
        return None
    return resolve_filing_targets(
        ref.ticker,
        [prior_target],
        use_cache=use_cache,
        cache_dir=cache_dir,
    )[prior_target]


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
