"""In-process TTL cache for expensive pipeline results."""

from __future__ import annotations

import os
import threading
import time
from collections import OrderedDict
from typing import Generic, TypeVar

T = TypeVar("T")


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "")
    if not raw.strip():
        return default
    return int(raw)


class TTLCache(Generic[T]):
    """Thread-safe TTL dict with FIFO eviction on max size."""

    def __init__(self, *, ttl_seconds: int, max_size: int) -> None:
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._lock = threading.Lock()
        # ponytail: FIFO via OrderedDict insertion order, not LRU
        self._entries: OrderedDict[tuple, tuple[T, float]] = OrderedDict()

    @property
    def enabled(self) -> bool:
        return self._ttl > 0 and self._max_size > 0

    def get(self, key: tuple) -> T | None:
        if not self.enabled:
            return None
        now = time.monotonic()
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if expires_at <= now:
                del self._entries[key]
                return None
            self._entries.move_to_end(key)
            return value

    def set(self, key: tuple, value: T) -> None:
        if not self.enabled:
            return
        expires_at = time.monotonic() + self._ttl
        with self._lock:
            self._entries[key] = (value, expires_at)
            self._entries.move_to_end(key)
            while len(self._entries) > self._max_size:
                self._entries.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


_metrics_cache: TTLCache | None = None
_metrics_cache_lock = threading.Lock()


def metrics_cache() -> TTLCache:
    global _metrics_cache
    if _metrics_cache is None:
        with _metrics_cache_lock:
            if _metrics_cache is None:
                _metrics_cache = TTLCache(
                    ttl_seconds=_env_int("METRICS_CACHE_TTL_SECONDS", 300),
                    max_size=_env_int("METRICS_CACHE_MAX_SIZE", 64),
                )
    return _metrics_cache


def metrics_cache_key(
    ticker: str,
    fiscal_year: int,
    form_type: str,
    quarter: str | None,
    compare_prior: bool,
) -> tuple:
    return (ticker.upper(), fiscal_year, form_type, quarter, compare_prior)
