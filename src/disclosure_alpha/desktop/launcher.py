"""Hidden browser launcher for the portable Windows application."""

from __future__ import annotations

import json
import os
import socket
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from typing import Callable

from disclosure_alpha.api.app_factory import create_app
from disclosure_alpha.desktop.settings import DesktopSession, desktop_data_dir, settings_path

_HEALTH_TIMEOUT_SECONDS = 20.0
_INSTANCE_FILE = "instance.json"


def _health_url(port: int) -> str:
    return f"http://127.0.0.1:{port}/health"


def _app_url(port: int) -> str:
    return f"http://127.0.0.1:{port}/app/"


def _is_healthy(port: int) -> bool:
    try:
        with urllib.request.urlopen(_health_url(port), timeout=0.75) as response:
            if response.status != 200:
                return False
            body = json.loads(response.read().decode("utf-8"))
            return body == {"status": "ok"}
    except (OSError, ValueError, json.JSONDecodeError, urllib.error.URLError):
        return False


def _find_open_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _instance_path(data_dir: Path) -> Path:
    return data_dir / _INSTANCE_FILE


def _load_running_port(data_dir: Path) -> int | None:
    path = _instance_path(data_dir)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        port = value.get("port") if isinstance(value, dict) else None
        if isinstance(port, int) and 0 < port < 65536 and _is_healthy(port):
            return port
    except (OSError, ValueError, json.JSONDecodeError):
        pass
    path.unlink(missing_ok=True)
    return None


def _write_instance(data_dir: Path, port: int) -> None:
    path = _instance_path(data_dir)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps({"pid": os.getpid(), "port": port}, sort_keys=True), encoding="utf-8"
    )
    os.replace(temporary, path)


def _remove_instance(data_dir: Path, port: int) -> None:
    path = _instance_path(data_dir)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(value, dict) and value.get("port") == port:
            path.unlink(missing_ok=True)
    except (OSError, ValueError, json.JSONDecodeError):
        path.unlink(missing_ok=True)


def _write_diagnostic(data_dir: Path, message: str) -> None:
    """Retain startup failures when a windowed executable has no console."""

    try:
        (data_dir / "launcher.log").write_text(message, encoding="utf-8")
    except OSError:
        pass


def _show_error(message: str, *, data_dir: Path | None = None) -> None:
    """Show startup errors despite PyInstaller's windowed/no-console mode."""

    if data_dir is not None:
        _write_diagnostic(data_dir, message)
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, message, "Disclosure Alpha", 0x10)
    else:  # pragma: no cover - convenience for local development
        print(message, file=sys.stderr)


def _wait_for_health(port: int, timeout_seconds: float = _HEALTH_TIMEOUT_SECONDS) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if _is_healthy(port):
            return True
        time.sleep(0.1)
    return False


def run_launcher(
    *,
    data_dir: Path | None = None,
    browser_open: Callable[[str], bool] = webbrowser.open,
    inactivity_seconds: float = 90.0,
) -> int:
    """Serve the local UI until its browser heartbeat expires.

    An instance record lets a second double-click focus an already-running UI
    instead of starting another hidden service.
    """

    runtime_dir = data_dir or desktop_data_dir()
    runtime_dir.mkdir(parents=True, exist_ok=True)
    existing_port = _load_running_port(runtime_dir)
    if existing_port is not None:
        browser_open(_app_url(existing_port))
        return 0

    session = DesktopSession(
        settings_path(runtime_dir), inactivity_seconds=inactivity_seconds
    )
    session.apply_environment()
    try:
        import uvicorn
    except ImportError:  # pragma: no cover - only possible in a broken build
        _show_error(
            "Disclosure Alpha could not start because its web server is missing.",
            data_dir=runtime_dir,
        )
        return 1

    port = _find_open_port()
    try:
        app = create_app(desktop_session=session)
    except Exception:
        _show_error(
            f"Disclosure Alpha could not configure its local review service.\n\n"
            f"{traceback.format_exc()}",
            data_dir=runtime_dir,
        )
        return 1
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host="127.0.0.1",
            port=port,
            # A PyInstaller windowed executable has no stderr stream. Uvicorn's
            # default logging config writes startup records there and aborts the
            # server before it can expose the UI.
            log_config=None,
            access_log=False,
        )
    )
    def serve() -> None:
        try:
            server.run()
        except Exception:
            _write_diagnostic(runtime_dir, traceback.format_exc())

    server_thread = threading.Thread(target=serve, name="DisclosureAlphaServer")
    server_thread.start()

    try:
        if not _wait_for_health(port):
            _show_error(
                "Disclosure Alpha could not start its local review service. "
                "See launcher.log in its local application-data folder for details.",
                data_dir=runtime_dir,
            )
            server.should_exit = True
            return 1
        _write_instance(runtime_dir, port)
        browser_open(_app_url(port))
        while server_thread.is_alive():
            if session.is_inactive():
                server.should_exit = True
            server_thread.join(timeout=1.0)
        return 0
    finally:
        server.should_exit = True
        server_thread.join(timeout=5.0)
        _remove_instance(runtime_dir, port)


def main() -> None:
    raise SystemExit(run_launcher())


if __name__ == "__main__":
    main()
