"""OpenBB Workspace FastAPI routes."""

from __future__ import annotations

import copy
import json
from importlib import resources
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse

from disclosure_alpha.api.endpoints.deps import parse_form_quarter, run_edgar, scores_dict
from disclosure_alpha.api.helpers import parse_scoring_model_version
from disclosure_alpha.openbb.adapters import (
    change_rows,
    flag_display_from_active,
    score_card_context,
)
from disclosure_alpha.openbb.demo import (
    demo_change_rows,
    demo_flag_rows,
    demo_score_card_context,
    is_demo,
)
from disclosure_alpha.openbb.render import render_company_html, render_error_html
from disclosure_alpha.pipeline import metrics_filing_ticker, score_for_model
from disclosure_alpha.version import SCORING_MODEL_VERSION

router = APIRouter(tags=["openbb"])


def _is_probe(request: Request) -> bool:
    """OpenBB widget validation hits endpoints with no query string."""
    return not request.url.query


@router.get("/")
def openbb_root() -> dict[str, str]:
    return {
        "name": "Disclosure Alpha",
        "status": "ok",
        "widgets": "/widgets.json",
        "apps": "/apps.json",
        "agents": "/agents.json",
        "prompts": "/prompts.json",
        "templates": "/templates.json",
        "health": "/health",
    }


def _load_packaged_json(name: str) -> Any:
    raw = resources.files("disclosure_alpha.openbb").joinpath(name).read_text(encoding="utf-8")
    return json.loads(raw)


@router.get("/widgets.json")
def get_widgets_json() -> JSONResponse:
    return JSONResponse(content=_load_packaged_json("widgets.json"))


@router.get("/apps.json")
def get_apps_json(request: Request) -> JSONResponse:
    apps = copy.deepcopy(_load_packaged_json("apps.json"))
    base = str(request.base_url).rstrip("/")
    if isinstance(apps, list):
        for app in apps:
            if not isinstance(app, dict):
                continue
            for srv in app.get("mcp_servers") or []:
                if isinstance(srv, dict):
                    url = srv.get("url", "")
                    if isinstance(url, str) and url.startswith("/"):
                        srv["url"] = f"{base}{url}"
    return JSONResponse(content=apps)


@router.get("/agents.json")
def get_agents_json() -> JSONResponse:
    return JSONResponse(content={})


@router.get("/prompts.json")
def get_prompts_json() -> JSONResponse:
    apps = _load_packaged_json("apps.json")
    prompts: list[str] = []
    if isinstance(apps, list):
        for app in apps:
            if isinstance(app, dict):
                prompts.extend(app.get("prompts") or [])
    return JSONResponse(content=prompts)


@router.get("/templates.json")
def get_templates_json() -> JSONResponse:
    return JSONResponse(content=[])


@router.get("/openbb/company", response_class=HTMLResponse)
def openbb_company(
    request: Request,
    ticker: str = Query("AAPL"),
    fiscal_year: int = Query(2025, ge=1994, le=2100),
    form_type: str = Query("10-K"),
    quarter: str | None = Query(None),
    demo: str | None = Query(None),
    scoring_model_version: str = Query(SCORING_MODEL_VERSION),
) -> HTMLResponse:
    if is_demo(demo) or _is_probe(request):
        ctx = demo_score_card_context(ticker)
        flag_display = flag_display_from_active(demo_flag_rows())
        return HTMLResponse(
            content=render_company_html(ctx, flag_display, demo_change_rows())
        )

    base, q = parse_form_quarter(form_type, quarter)
    try:
        scoring_version = parse_scoring_model_version(scoring_model_version)
    except ValueError as exc:
        return HTMLResponse(
            content=render_error_html(422, str(exc)),
            status_code=422,
        )

    def _fetch() -> HTMLResponse:
        result = metrics_filing_ticker(
            ticker,
            fiscal_year,
            form_type=base,
            quarter=q,
            compare_prior=True,
        )
        scores = score_for_model(result.metrics, scoring_version, form_type=base)
        scores_payload = scores_dict(scores)
        versions = dict(result.versions)
        versions["scoring_model_version"] = scoring_version
        filing = result.filing or {
            "ticker": ticker.upper(),
            "fiscal_year": fiscal_year,
            "form_type": base,
        }
        ctx = score_card_context(filing, scores_payload, versions)
        from disclosure_alpha.api.shapes import shape_flags_payload

        flag_display = flag_display_from_active(
            shape_flags_payload(result.metrics)["active_flags"]
        )
        changes = change_rows(result.metrics, scores)
        return HTMLResponse(content=render_company_html(ctx, flag_display, changes))

    try:
        return run_edgar(_fetch)
    except HTTPException as exc:
        return HTMLResponse(
            content=render_error_html(exc.status_code, str(exc.detail)),
            status_code=exc.status_code,
        )
