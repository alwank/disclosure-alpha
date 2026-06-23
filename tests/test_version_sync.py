"""Package version must match pyproject.toml and editable-install fallback."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import disclosure_alpha

_ROOT = Path(__file__).resolve().parents[1]
_INIT = _ROOT / "src" / "disclosure_alpha" / "__init__.py"


def test_package_version_matches_pyproject() -> None:
    data = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert disclosure_alpha.__version__ == data["project"]["version"]


def test_editable_fallback_matches_pyproject() -> None:
    data = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    expected = data["project"]["version"]
    match = re.search(r'__version__ = "([^"]+)"\s+# editable install fallback', _INIT.read_text())
    assert match is not None
    assert match.group(1) == expected
