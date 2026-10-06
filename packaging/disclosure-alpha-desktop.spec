# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller recipe for the Windows portable folder."""

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files


# SPECPATH is the directory that contains this .spec file.
ROOT = Path(SPECPATH).parent
PACKAGE_ROOT = ROOT / "src"
ENTRY_POINT = ROOT / "packaging" / "desktop_launcher.py"

# StaticFiles needs physical files, so Vite's generated web_assets directory is
# collected alongside the Python package rather than left inside the PYZ archive.
datas = collect_data_files("disclosure_alpha")
# Uvicorn resolves these implementations by name at runtime. Everything else is
# imported through the normal API and pipeline import graph.
hiddenimports = [
    "lxml.etree",
    "uvicorn.lifespan.on",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
]
console = os.environ.get("DISCLOSURE_ALPHA_DEBUG_CONSOLE") == "1"

a = Analysis(
    [str(ENTRY_POINT)],
    pathex=[str(PACKAGE_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["spacy", "sentence_transformers"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    name="Disclosure Alpha",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=console,
    exclude_binaries=True,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="Disclosure Alpha",
)
