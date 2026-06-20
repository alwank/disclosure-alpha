from disclosure_alpha.api.endpoints.changes import router as changes_router
from disclosure_alpha.api.endpoints.filings import router as filings_router
from disclosure_alpha.api.endpoints.flags import router as flags_router
from disclosure_alpha.api.endpoints.health import router as health_router
from disclosure_alpha.api.endpoints.matrix import router as matrix_router
from disclosure_alpha.api.endpoints.metrics import router as metrics_router
from disclosure_alpha.api.endpoints.panel import router as panel_router
from disclosure_alpha.api.endpoints.sections import router as sections_router

ROUTERS = [
    health_router,
    filings_router,
    sections_router,
    metrics_router,
    matrix_router,
    flags_router,
    changes_router,
    panel_router,
]
