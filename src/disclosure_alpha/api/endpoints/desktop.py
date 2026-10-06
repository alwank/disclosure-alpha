"""Local-only configuration endpoints used by the portable desktop launcher."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from disclosure_alpha.desktop.settings import DesktopSession


class DesktopSettingsRequest(BaseModel):
    display_name: str = Field(max_length=120)
    email: str = Field(max_length=254)


class DesktopSettingsResponse(BaseModel):
    configured: bool
    display_name: str | None = None


def create_router(session: DesktopSession) -> APIRouter:
    """Create routes only for an app explicitly started by the desktop launcher."""

    router = APIRouter(prefix="/v1/desktop", tags=["desktop"])

    @router.get("/settings", response_model=DesktopSettingsResponse)
    def get_settings() -> DesktopSettingsResponse:
        settings = session.settings
        return DesktopSettingsResponse(
            configured=settings is not None,
            display_name=settings.display_name if settings else None,
        )

    @router.put("/settings", response_model=DesktopSettingsResponse)
    def put_settings(request: DesktopSettingsRequest) -> DesktopSettingsResponse:
        try:
            settings = session.update_settings(request.display_name, request.email)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        session.touch()
        return DesktopSettingsResponse(configured=True, display_name=settings.display_name)

    @router.post("/heartbeat", status_code=204, response_class=Response)
    def heartbeat() -> Response:
        session.touch()
        return Response(status_code=204)

    return router
