from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

from disclosure_alpha.edgar.types import SecFetchError

SEC_BASE = "https://www.sec.gov"
DATA_BASE = "https://data.sec.gov"
_MIN_INTERVAL = 0.11  # ponytail: ~9 req/s global lock; fine for single-user self-host
_last_request_at = 0.0


def _user_agent() -> str:
    ua = os.environ.get("SEC_USER_AGENT", "").strip()
    if not ua:
        raise SecFetchError(
            "SEC_USER_AGENT env var required (e.g. 'YourName your@email.com')"
        )
    return ua


def _throttle() -> None:
    global _last_request_at
    elapsed = time.monotonic() - _last_request_at
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _last_request_at = time.monotonic()


def fetch_json(url: str) -> Any:
    _throttle()
    req = urllib.request.Request(url, headers={"User-Agent": _user_agent(), "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise SecFetchError(f"SEC HTTP {exc.code} for {url}") from exc
    except urllib.error.URLError as exc:
        raise SecFetchError(f"SEC fetch failed for {url}: {exc.reason}") from exc


def fetch_text(url: str) -> str:
    _throttle()
    req = urllib.request.Request(url, headers={"User-Agent": _user_agent(), "Accept": "text/html,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise SecFetchError(f"SEC HTTP {exc.code} for {url}") from exc
    except urllib.error.URLError as exc:
        raise SecFetchError(f"SEC fetch failed for {url}: {exc.reason}") from exc


def fetch_company_tickers() -> dict[str, tuple[str, str]]:
    """Return ticker -> (cik_padded, company_name)."""
    data = fetch_json(f"{SEC_BASE}/files/company_tickers.json")
    out: dict[str, tuple[str, str]] = {}
    for entry in data.values():
        ticker = str(entry["ticker"]).upper()
        cik = str(entry["cik_str"]).zfill(10)
        out[ticker] = (cik, str(entry.get("title", "")))
    return out


def fetch_submissions(cik: str) -> dict[str, Any]:
    cik_padded = cik.zfill(10)
    return fetch_json(f"{DATA_BASE}/submissions/CIK{cik_padded}.json")


def filing_document_url(cik: str, accession_number: str, primary_document: str) -> str:
    cik_stripped = cik.lstrip("0") or "0"
    acc_nodash = accession_number.replace("-", "")
    return f"{SEC_BASE}/Archives/edgar/data/{cik_stripped}/{acc_nodash}/{primary_document}"
