"""Optional per-stage timing for metrics_filing_ticker (PIPELINE_TIMING=1)."""

from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager
from typing import Iterator

logger = logging.getLogger(__name__)


def _timing_logger() -> logging.Logger:
    # ponytail: uvicorn.error is visible in disclosure-alpha-api terminal without log setup
    if pipeline_timing_enabled():
        return logging.getLogger("uvicorn.error")
    return logger


def pipeline_timing_enabled() -> bool:
    return os.getenv("PIPELINE_TIMING", "").strip().lower() in ("1", "true", "yes")


class PipelineTimer:
    def __init__(self, label: str) -> None:
        self.label = label
        self.enabled = pipeline_timing_enabled()
        self.stages: dict[str, float] = {}
        self._start = time.perf_counter()

    @contextmanager
    def stage(self, name: str) -> Iterator[None]:
        if not self.enabled:
            yield
            return
        t0 = time.perf_counter()
        try:
            yield
        finally:
            self.stages[name] = self.stages.get(name, 0.0) + (time.perf_counter() - t0)

    def log(self, **extra: object) -> None:
        if not self.enabled:
            return
        total = time.perf_counter() - self._start
        parts = " ".join(f"{name}={secs:.2f}s" for name, secs in sorted(self.stages.items()))
        tail = " ".join(f"{key}={value}" for key, value in extra.items())
        msg = f"pipeline_timing {self.label} total={total:.2f}s"
        if parts:
            msg += f" {parts}"
        if tail:
            msg += f" {tail}"
        _timing_logger().info(msg)


def log_cache_hit(label: str) -> None:
    if pipeline_timing_enabled():
        _timing_logger().info("pipeline_timing %s cache=hit", label)
