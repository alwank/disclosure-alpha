"""Per-user settings for the portable desktop launcher."""

from __future__ import annotations

import json
import os
import re
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from disclosure_alpha import __version__

APP_NAME = "Disclosure Alpha"
DESKTOP_MODE_ENV = "DISCLOSURE_ALPHA_DESKTOP"
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class DesktopSettings:
    """The minimum contact information required for SEC EDGAR requests."""

    display_name: str
    email: str

    @property
    def user_agent(self) -> str:
        return f"Disclosure Alpha/{__version__} ({self.display_name} {self.email})"


def _clean_display_name(value: str) -> str:
    clean = " ".join(value.split())
    if not clean or len(clean) > 120 or any(ord(char) < 32 for char in clean):
        raise ValueError("Enter a name between 1 and 120 characters.")
    return clean


def _clean_email(value: str) -> str:
    clean = value.strip()
    if len(clean) > 254 or not _EMAIL_RE.fullmatch(clean):
        raise ValueError("Enter a valid contact email address.")
    return clean


def make_settings(display_name: str, email: str) -> DesktopSettings:
    return DesktopSettings(
        display_name=_clean_display_name(display_name),
        email=_clean_email(email),
    )


def desktop_data_dir(environ: Mapping[str, str] | None = None) -> Path:
    """Return a writable, upgrade-stable directory outside the ZIP folder."""

    values = environ if environ is not None else os.environ
    local_app_data = values.get("LOCALAPPDATA") or values.get("APPDATA")
    if local_app_data:
        return Path(local_app_data) / APP_NAME
    # This is only a fallback for non-Windows development and tests.
    return Path.home() / ".local" / "share" / "disclosure-alpha"


def settings_path(data_dir: Path | None = None) -> Path:
    return (data_dir or desktop_data_dir()) / "settings.json"


def load_settings(path: Path) -> DesktopSettings | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            return None
        display_name = value.get("display_name")
        email = value.get("email")
        if not isinstance(display_name, str) or not isinstance(email, str):
            return None
        return make_settings(display_name, email)
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def save_settings(path: Path, settings: DesktopSettings) -> None:
    """Atomically replace settings so an interrupted write cannot corrupt setup."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        {"display_name": settings.display_name, "email": settings.email},
        indent=2,
        sort_keys=True,
    )
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as temporary:
        temporary.write(f"{payload}\n")
        temporary_path = Path(temporary.name)
    try:
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


class DesktopSession:
    """Settings and UI liveness shared by the desktop launcher and local routes."""

    def __init__(self, path: Path, *, inactivity_seconds: float = 90.0):
        self.path = path
        self.inactivity_seconds = inactivity_seconds
        self._lock = threading.Lock()
        self._settings = load_settings(path)
        self._last_heartbeat = time.monotonic()

    @property
    def settings(self) -> DesktopSettings | None:
        with self._lock:
            return self._settings

    @property
    def configured(self) -> bool:
        return self.settings is not None

    def update_settings(self, display_name: str, email: str) -> DesktopSettings:
        settings = make_settings(display_name, email)
        save_settings(self.path, settings)
        with self._lock:
            self._settings = settings
        os.environ["SEC_USER_AGENT"] = settings.user_agent
        return settings

    def apply_environment(self) -> Path:
        """Configure runtime paths before the pipeline makes any SEC requests."""

        data_dir = self.path.parent
        cache_dir = data_dir / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ[DESKTOP_MODE_ENV] = "1"
        os.environ["DISCLOSURE_ALPHA_CACHE_DIR"] = str(cache_dir)
        current = self.settings
        if current is not None:
            os.environ["SEC_USER_AGENT"] = current.user_agent
        else:
            os.environ.pop("SEC_USER_AGENT", None)
        return cache_dir

    def touch(self) -> None:
        with self._lock:
            self._last_heartbeat = time.monotonic()

    def is_inactive(self) -> bool:
        with self._lock:
            return time.monotonic() - self._last_heartbeat > self.inactivity_seconds
