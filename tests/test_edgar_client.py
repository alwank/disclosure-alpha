from __future__ import annotations

import json
import threading
import time
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from disclosure_alpha.edgar import client
from disclosure_alpha.edgar.types import SecFetchError


def _mock_json_response(payload: dict) -> MagicMock:
    resp = MagicMock()
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    resp.read.return_value = json.dumps(payload).encode("utf-8")
    return resp


def test_fetch_json_requires_user_agent(monkeypatch):
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    with pytest.raises(SecFetchError, match="SEC_USER_AGENT"):
        client.fetch_json("https://www.sec.gov/example.json")


@patch("urllib.request.urlopen")
def test_fetch_json_http_error(mock_urlopen, monkeypatch):
    monkeypatch.setenv("SEC_USER_AGENT", "TestOrg test@example.com")
    mock_urlopen.side_effect = urllib.error.HTTPError(
        "url", 503, "Service Unavailable", {}, None
    )
    with pytest.raises(SecFetchError, match="HTTP 503"):
        client.fetch_json("https://www.sec.gov/example.json")


@patch("urllib.request.urlopen")
def test_fetch_text_url_error(mock_urlopen, monkeypatch):
    monkeypatch.setenv("SEC_USER_AGENT", "TestOrg test@example.com")
    mock_urlopen.side_effect = urllib.error.URLError("connection reset")
    with pytest.raises(SecFetchError, match="fetch failed"):
        client.fetch_text("https://www.sec.gov/example.htm")


@patch("urllib.request.urlopen")
def test_throttle_enforces_min_interval(mock_urlopen, monkeypatch):
    monkeypatch.setenv("SEC_USER_AGENT", "TestOrg test@example.com")
    mock_urlopen.return_value = _mock_json_response({"ok": True})
    client._last_request_at = 0.0

    sleeps: list[float] = []
    ticks = iter([0.0, 0.0, 0.05, 0.05])

    with patch.object(time, "monotonic", lambda: next(ticks)):
        with patch.object(time, "sleep", lambda d: sleeps.append(d)):
            client.fetch_json("https://www.sec.gov/one.json")
            client.fetch_json("https://www.sec.gov/two.json")

    assert sleeps == [pytest.approx(client._MIN_INTERVAL), pytest.approx(client._MIN_INTERVAL - 0.05)]


@patch("urllib.request.urlopen")
def test_throttle_serializes_concurrent_requests(mock_urlopen, monkeypatch):
    monkeypatch.setenv("SEC_USER_AGENT", "TestOrg test@example.com")
    mock_urlopen.return_value = _mock_json_response({"ok": True})
    client._last_request_at = 0.0

    barrier = threading.Barrier(2)
    errors: list[BaseException] = []

    def worker():
        try:
            barrier.wait(timeout=2)
            client.fetch_json("https://www.sec.gov/concurrent.json")
        except BaseException as exc:
            errors.append(exc)

    with patch.object(time, "sleep", lambda _d: None):
        threads = [threading.Thread(target=worker) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

    assert not errors
    assert mock_urlopen.call_count == 2
