"""Fail the release if the built filing reader is absent from source and wheel archives."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from tarfile import open as open_tar
from zipfile import ZipFile


def main() -> None:
    with Path("pyproject.toml").open("rb") as source:
        version = tomllib.load(source)["project"]["version"]
    artifacts = list(Path("dist").glob("disclosure_alpha-*.whl"))
    sources = list(Path("dist").glob("disclosure_alpha-*.tar.gz"))
    if len(artifacts) != 1 or len(sources) != 1:
        raise SystemExit("Expected one Disclosure Alpha wheel and one source archive")
    if not artifacts[0].name.startswith(f"disclosure_alpha-{version}-"):
        raise SystemExit("Wheel version does not match pyproject.toml")
    if sources[0].name != f"disclosure_alpha-{version}.tar.gz":
        raise SystemExit("Source archive version does not match pyproject.toml")
    with ZipFile(artifacts[0]) as archive:
        names = set(archive.namelist())
        index_path = "disclosure_alpha/web_assets/index.html"
        if index_path not in names:
            raise SystemExit("Wheel is missing the filing review index.html")
        index = archive.read(index_path).decode("utf-8")
        asset_urls = re.findall(r'["\'](/app/assets/[^"\']+)["\']', index)
        if (
            not asset_urls
            or not any(url.endswith(".js") for url in asset_urls)
            or not any(url.endswith(".css") for url in asset_urls)
        ):
            raise SystemExit("Wheel index is missing linked JS/CSS assets")
        for url in asset_urls:
            path = "disclosure_alpha/web_assets/" + url.removeprefix("/app/")
            if path not in names or not archive.read(path):
                raise SystemExit(f"Wheel is missing linked asset: {url}")
    with open_tar(sources[0]) as archive:
        names = set(archive.getnames())
        prefix = f"disclosure_alpha-{version}/src/disclosure_alpha/web_assets/"
        if prefix + "index.html" not in names:
            raise SystemExit("Source archive is missing the filing review index.html")
        for url in asset_urls:
            path = prefix + url.removeprefix("/app/")
            member = archive.extractfile(path) if path in names else None
            if member is None or not member.read():
                raise SystemExit(f"Source archive is missing linked asset: {url}")
    print("Current filing review assets are present in wheel and source archive")


if __name__ == "__main__":
    main()
