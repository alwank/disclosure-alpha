"""Portable desktop settings, routes, and launcher behavior."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from disclosure_alpha.api.app_factory import create_app
from disclosure_alpha.desktop import launcher
from disclosure_alpha.desktop.settings import (
    DesktopSession,
    desktop_data_dir,
    load_settings,
    make_settings,
    save_settings,
    settings_path,
)


def test_settings_are_persisted_and_generate_a_sec_user_agent(tmp_path):
    path = settings_path(tmp_path)
    settings = make_settings("Jane  Analyst", "jane@example.com")
    save_settings(path, settings)

    assert load_settings(path) == settings
    assert settings.user_agent.startswith("Disclosure Alpha/")
    assert settings.user_agent.endswith("(Jane Analyst jane@example.com)")


@pytest.mark.parametrize(
    ("display_name", "email"),
    [("", "jane@example.com"), ("Jane", "not-an-email"), ("\x01", "jane@example.com")],
)
def test_settings_reject_invalid_sec_contact(display_name, email):
    with pytest.raises(ValueError):
        make_settings(display_name, email)


def test_desktop_uses_local_app_data_for_settings_and_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    data_dir = desktop_data_dir()
    session = DesktopSession(settings_path(data_dir))
    cache_dir = session.apply_environment()

    assert data_dir == tmp_path / "Disclosure Alpha"
    assert cache_dir == data_dir / "cache"
    assert cache_dir.is_dir()
    assert session.path.parent == data_dir


def test_desktop_routes_are_only_mounted_for_desktop_session(tmp_path, monkeypatch):
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    with patch("disclosure_alpha.api.app_factory.try_create_analyst_mcp", return_value=None):
        with TestClient(create_app()) as ordinary_client:
            assert ordinary_client.get("/v1/desktop/settings").status_code == 404

        session = DesktopSession(settings_path(tmp_path))
        with TestClient(create_app(desktop_session=session)) as client:
            assert client.get("/v1/desktop/settings").json() == {
                "configured": False,
                "display_name": None,
            }
            saved = client.put(
                "/v1/desktop/settings",
                json={"display_name": "Jane Analyst", "email": "jane@example.com"},
            )
            assert saved.status_code == 200
            assert saved.json() == {"configured": True, "display_name": "Jane Analyst"}
            invalid = client.put(
                "/v1/desktop/settings",
                json={"display_name": "Jane Analyst", "email": "not-an-email"},
            )
            assert invalid.status_code == 422
            assert client.post("/v1/desktop/heartbeat").status_code == 204

    assert load_settings(session.path) == make_settings("Jane Analyst", "jane@example.com")
    assert "Jane Analyst jane@example.com" in session.settings.user_agent  # type: ignore[union-attr]


def test_launcher_reuses_a_healthy_existing_instance(tmp_path, monkeypatch):
    port = 45678
    (tmp_path / "instance.json").write_text(
        json.dumps({"pid": 123, "port": port}), encoding="utf-8"
    )
    monkeypatch.setattr(launcher, "_is_healthy", lambda value: value == port)
    opened: list[str] = []

    result = launcher.run_launcher(
        data_dir=tmp_path,
        browser_open=lambda url: opened.append(url) or True,
    )

    assert result == 0
    assert opened == [f"http://127.0.0.1:{port}/app/"]


def test_launcher_starts_loopback_server_and_removes_its_instance_file(
    tmp_path, monkeypatch
):
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    monkeypatch.setattr(launcher, "create_app", lambda **_kwargs: app)
    opened: list[str] = []

    def open_browser(url: str) -> bool:
        opened.append(url)
        port = int(url.split(":")[2].split("/")[0])
        assert launcher._is_healthy(port)
        return True

    result = launcher.run_launcher(
        data_dir=tmp_path,
        browser_open=open_browser,
        inactivity_seconds=0.01,
    )

    assert result == 0
    assert len(opened) == 1
    assert not (tmp_path / "instance.json").exists()
