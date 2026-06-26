import logging

import pytest

from disclosure_alpha.pipeline_timing import PipelineTimer, log_cache_hit, pipeline_timing_enabled


def test_pipeline_timing_disabled_by_default(monkeypatch):
    monkeypatch.delenv("PIPELINE_TIMING", raising=False)
    assert pipeline_timing_enabled() is False


def test_pipeline_timing_enabled(monkeypatch):
    monkeypatch.setenv("PIPELINE_TIMING", "1")
    assert pipeline_timing_enabled() is True


def test_pipeline_timer_accumulates_stages(monkeypatch, caplog):
    monkeypatch.setenv("PIPELINE_TIMING", "1")
    caplog.set_level(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    timer = PipelineTimer("TEST AAPL")
    with timer.stage("edgar"):
        with timer.stage("parse"):
            pass
    timer.log(sections=3)
    assert "pipeline_timing TEST AAPL" in caplog.text
    assert "edgar=" in caplog.text
    assert "parse=" in caplog.text
    assert "sections=3" in caplog.text


def test_pipeline_timer_no_log_when_disabled(monkeypatch, caplog):
    monkeypatch.delenv("PIPELINE_TIMING", raising=False)
    caplog.set_level(logging.INFO)
    timer = PipelineTimer("silent")
    with timer.stage("edgar"):
        pass
    timer.log()
    assert "pipeline_timing" not in caplog.text


def test_log_cache_hit(monkeypatch, caplog):
    monkeypatch.setenv("PIPELINE_TIMING", "1")
    caplog.set_level(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    log_cache_hit("AAPL FY2025 10-K compare_prior=True")
    assert "cache=hit" in caplog.text
