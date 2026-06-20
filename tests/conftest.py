import os
from pathlib import Path

import pytest

from html_fixtures import minimal_10k_html, minimal_prior_html, write_temp_html

os.environ.setdefault("EMBEDDING_BACKEND", "tfidf")

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "filings"


@pytest.fixture
def minimal_html() -> str:
    return minimal_10k_html()


@pytest.fixture
def prior_html() -> str:
    return minimal_prior_html()


@pytest.fixture
def aapl_fixture_path() -> Path:
    return FIXTURES_DIR / "aapl_2025_10k.html"
