"""Sphinx configuration for Disclosure Alpha documentation."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath("../src"))

import disclosure_alpha

project = "disclosure-alpha"
copyright = "Disclosure Alpha contributors"
author = "Disclosure Alpha"
release = disclosure_alpha.__version__
html_title = "disclosure-alpha"

_repo_url = os.environ.get(
    "READTHEDOCS_GIT_REPOSITORY_URL",
    "https://github.com/alwank/disclosure-alpha",
).removesuffix(".git")
_repo_name = _repo_url.rsplit("/", maxsplit=2)[-2] + "/" + _repo_url.rsplit("/", maxsplit=1)[-1]

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinxext.rediraffe",
    "sphinx_immaterial",
]

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "_includes/**",
    "examples/*.json",  # raw fixtures; gallery page links to them
    "Thumbs.db",
    ".DS_Store",
    "postman",
    "README.md",
    "readthedocs-public-docs-improvement-plan.md",
    "codebase-audit-report.md",  # repo-only audit; not public RTD nav
    # Contributor / repo-only (not public RTD pages)
    "CONTRIBUTING_DOCS.md",
    "developer/**",
    # Draft or internal methodology (not public until complete)
    "methodology/roadmap/**",
    "methodology/dictionaries/**",
    "appendix/index.md",
]

linkcheck_ignore = [
    # DOI resolvers block automated clients (403)
    r"https://doi\.org/.*",
    # SEC pages block linkcheck bots (403)
    r"https://www\.sec\.gov/.*",
    # MCP docs redirect to a deeper URL
    r"https://modelcontextprotocol\.io/.*",
]

source_suffix = {
    ".md": "markdown",
}

root_doc = "index"

html_theme = "sphinx_immaterial"
html_static_path = ["_static"]
html_theme_options = {
    "site_url": "https://disclosure-alpha.readthedocs.io/",
    "repo_url": _repo_url,
    "repo_name": _repo_name,
    "edit_uri": "edit/main/docs/",
    "palette": [
        {
            "media": "(prefers-color-scheme: light)",
            "scheme": "default",
            "primary": "black",
            "accent": "teal",
            "toggle": {
                "icon": "material/brightness-7",
                "name": "Switch to dark mode",
            },
        },
        {
            "media": "(prefers-color-scheme: dark)",
            "scheme": "slate",
            "primary": "black",
            "accent": "teal",
            "toggle": {
                "icon": "material/brightness-4",
                "name": "Switch to light mode",
            },
        },
    ],
    "features": [
        "navigation.sections",
        "navigation.expand",
        "content.code.copy",
        "toc.follow",
    ],
    "icon": {
        "repo": "fontawesome/brands/github",
    },
}

myst_heading_anchors = 3
suppress_warnings = ["myst.xref_missing", "misc.highlighting_failure"]

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": False,
    "member-order": "bysource",
}

rediraffe_redirects = {
    "01_overview.md": "methodology/overview.md",
    "02_research_foundation.md": "methodology/research-foundation.md",
    "03_metrics_spec.md": "methodology/metrics-engine.md",
    "04_diff_spec.md": "methodology/diff-engine.md",
    "05_aggregation_spec.md": "methodology/aggregation.md",
    "06_v2_improvement_plan.md": "methodology/overview.md",
    "07_validation_protocol.md": "validation/evidence-and-limitations.md",
    "08_dictionary_enrichment_research.md": "methodology/metrics-engine.md",
    "09_product_surfaces.md": "getting-started/choose-your-surface.md",
    "getting-started/hosted-vs-self-hosted.md": "getting-started/choose-your-surface.md",
    "reference/oss-score-catalog.md": "reference/score-catalog.md",
}
