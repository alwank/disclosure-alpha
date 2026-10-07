"""Check the installed wheel serves its UI and filing review route."""

from __future__ import annotations

import re

from fastapi.testclient import TestClient

from disclosure_alpha.api.routes import app


def main() -> None:
    with TestClient(app) as client:
        page = client.get("/app/")
        assert page.status_code == 200, page.text
        asset_paths = re.findall(r'["\'](/app/assets/[^"\']+)["\']', page.text)
        assert asset_paths, "UI page has no linked assets"
        for path in asset_paths:
            asset = client.get(path)
            assert asset.status_code == 200, f"Asset unavailable: {path}"
            assert asset.content, f"Asset is empty: {path}"

        review_path = "/v1/company/AAPL/filing-review"
        assert review_path.replace("AAPL", "{ticker}") in app.openapi()["paths"]
        invalid = client.get(
            review_path,
            params={"fiscal_year": 2025, "form_type": "8-K"},
        )
        assert invalid.status_code == 422, invalid.text

    print("Installed wheel serves /app/, linked assets, and the filing review route")


if __name__ == "__main__":
    main()
