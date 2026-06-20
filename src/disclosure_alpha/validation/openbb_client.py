"""Thin HTTP client for a local OpenBB Platform API."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

DEFAULT_OPENBB_API_URL = "http://127.0.0.1:6900"


class OpenBBError(RuntimeError):
    pass


class OpenBBClient:
    def __init__(self, base_url: str | None = None, *, timeout: float = 60.0) -> None:
        self.base_url = (base_url or os.environ.get("OPENBB_API_URL", DEFAULT_OPENBB_API_URL)).rstrip(
            "/"
        )
        self.timeout = timeout

    def get(self, path: str, **params: Any) -> dict[str, Any]:
        query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        url = f"{self.base_url}{path}"
        if query:
            url = f"{url}?{query}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                payload = json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")
            raise OpenBBError(f"OpenBB HTTP {exc.code}: {body[:500]}") from exc
        except urllib.error.URLError as exc:
            raise OpenBBError(f"OpenBB unreachable at {self.base_url}: {exc}") from exc

        if isinstance(payload, dict) and payload.get("detail") and not payload.get("results"):
            detail = payload["detail"]
            if isinstance(detail, str):
                raise OpenBBError(detail)
        return payload

    def equity_price_historical(
        self,
        symbol: str,
        *,
        start_date: str,
        end_date: str,
        provider: str = "yfinance",
    ) -> list[dict[str, Any]]:
        data = self.get(
            "/api/v1/equity/price/historical",
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            provider=provider,
        )
        results = data.get("results")
        return results if isinstance(results, list) else []

    def health_check(self) -> bool:
        try:
            self.get("/api/v1/coverage/commands")
            return True
        except OpenBBError:
            return False
