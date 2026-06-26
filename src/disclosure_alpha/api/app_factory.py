from __future__ import annotations

import contextlib
import os

# ponytail: API-only defaults; CLI/SDK callers keep model/timing defaults unless they set env
os.environ.setdefault("EMBEDDING_BACKEND", "tfidf")
os.environ.setdefault("PIPELINE_TIMING", "1")

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response

from disclosure_alpha import __version__
from disclosure_alpha.api.endpoints import ROUTERS
from disclosure_alpha.mcp.http_mount import try_create_analyst_mcp

_DEFAULT_OPENBB_ORIGINS = (
    "https://pro.openbb.co",
    "https://pro.openbb.dev",
    "http://localhost:3000",
)


def _openbb_cors_origins() -> list[str]:
    raw = os.environ.get("OPENBB_CORS_ORIGINS", "")
    if raw.strip():
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return list(_DEFAULT_OPENBB_ORIGINS)


def _cors_headers_for(request: Request) -> dict[str, str]:
    origin = request.headers.get("origin")
    if origin and origin in _openbb_cors_origins():
        return {
            "access-control-allow-origin": origin,
            "access-control-allow-credentials": "true",
            "vary": "Origin",
        }
    return {}


class _PrivateNetworkAccessMiddleware(BaseHTTPMiddleware):
    """Chrome blocks https://pro.openbb.co → http://127.0.0.1 without this preflight header."""

    async def dispatch(self, request: StarletteRequest, call_next) -> Response:
        origin = request.headers.get("origin", "")
        pna = request.headers.get("access-control-request-private-network", "").lower() == "true"
        if (
            request.method == "OPTIONS"
            and pna
            and origin in _openbb_cors_origins()
        ):
            return Response(
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Allow-Methods": request.headers.get(
                        "access-control-request-method", "GET"
                    ),
                    "Access-Control-Allow-Headers": request.headers.get(
                        "access-control-request-headers", "*"
                    ),
                    "Access-Control-Allow-Private-Network": "true",
                    "Vary": "Origin",
                },
            )
        response = await call_next(request)
        if origin in _openbb_cors_origins():
            response.headers["Access-Control-Allow-Private-Network"] = "true"
        return response


def create_app() -> FastAPI:
    analyst_mcp = try_create_analyst_mcp()

    @contextlib.asynccontextmanager
    async def lifespan(_app: FastAPI):
        if analyst_mcp is not None:
            async with analyst_mcp.session_manager.run():
                yield
        else:
            yield

    app = FastAPI(
        title="Disclosure Alpha API",
        description="Self-hosted deterministic SEC filing analytics",
        version=__version__,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_openbb_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Mcp-Session-Id"],
    )
    # Outermost on response: patch CORS preflight after CORSMiddleware builds it.
    app.add_middleware(_PrivateNetworkAccessMiddleware)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers={**_cors_headers_for(request), **(exc.headers or {})},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # ponytail: Starlette 500 path skips CORSMiddleware; attach headers so Workspace
        # shows the real error instead of a generic CORS failure.
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
            headers=_cors_headers_for(request),
        )

    for router in ROUTERS:
        app.include_router(router)

    if analyst_mcp is not None:
        analyst_mcp.settings.streamable_http_path = "/"
        app.mount("/mcp", analyst_mcp.streamable_http_app())

    return app
