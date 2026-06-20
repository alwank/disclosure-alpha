from __future__ import annotations

from fastapi import FastAPI

from disclosure_alpha.api.endpoints import ROUTERS


def create_app() -> FastAPI:
    app = FastAPI(
        title="Disclosure Alpha API",
        description="Self-hosted deterministic SEC filing analytics",
        version="1.0.0",
    )
    for router in ROUTERS:
        app.include_router(router)
    return app
