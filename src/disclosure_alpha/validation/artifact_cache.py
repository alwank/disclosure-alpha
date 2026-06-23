"""Disk cache helpers for validation artifacts."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


def cache_dir() -> Path:
    return Path(
        os.environ.get("DISCLOSURE_ALPHA_VALIDATION_CACHE_DIR", "data/validation/cache")
    )


def cache_key(*parts: str) -> str:
    joined = "|".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def read_json(key: str) -> dict[str, Any] | None:
    path = cache_dir() / f"{key}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(key: str, payload: dict[str, Any]) -> Path:
    out = cache_dir() / f"{key}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload), encoding="utf-8")
    return out
