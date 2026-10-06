"""Fail the release if the built filing reader is absent from source and wheel archives."""

from __future__ import annotations

from pathlib import Path
from tarfile import open as open_tar
from zipfile import ZipFile


def main() -> None:
    artifacts = list(Path("dist").glob("disclosure_alpha-*.whl"))
    sources = list(Path("dist").glob("disclosure_alpha-*.tar.gz"))
    if len(artifacts) != 1 or len(sources) != 1:
        raise SystemExit("Expected one Disclosure Alpha wheel and one source archive")
    with ZipFile(artifacts[0]) as archive:
        names = archive.namelist()
        if "disclosure_alpha/web_assets/index.html" not in names:
            raise SystemExit("Wheel is missing the filing review index.html")
        if not any(name.startswith("disclosure_alpha/web_assets/assets/") for name in names):
            raise SystemExit("Wheel is missing the filing review JS/CSS assets")
    with open_tar(sources[0]) as archive:
        names = archive.getnames()
        if not any(name.endswith("src/disclosure_alpha/web_assets/index.html") for name in names):
            raise SystemExit("Source archive is missing the filing review index.html")
    print("Filing review assets are present in wheel and source archive")


if __name__ == "__main__":
    main()
