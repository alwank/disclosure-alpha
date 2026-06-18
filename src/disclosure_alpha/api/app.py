"""Self-hosted HTTP API for Disclosure Alpha."""

from __future__ import annotations

import os


def main() -> None:
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "API extras required: pip install disclosure-alpha[api]"
        ) from exc

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("disclosure_alpha.api.routes:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
