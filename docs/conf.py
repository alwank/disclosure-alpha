"""Sphinx configuration for Disclosure Alpha documentation."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath("../src"))

import disclosure_alpha

project = "Disclosure Alpha"
copyright = "Disclosure Alpha contributors"
author = "Disclosure Alpha"
release = disclosure_alpha.__version__

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinxext.rediraffe",
    "sphinx_copybutton",
]

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "_includes/**",
    "examples/**",
    "Thumbs.db",
    ".DS_Store",
    "postman",
    "README.md",
    "developer/index.md",
    "methodology/roadmap/**",
    "methodology/dictionaries/**",
    "reference/python/validation.md",
    "reference/http/schemas/**",
    "guides/http/endpoints/**",
    "appendix/index.md",
]

source_suffix = {
    ".md": "markdown",
}

root_doc = "index"

html_theme = "furo"
html_static_path = ["_static"]
html_theme_options = {
    "sidebar_hide_name": False,
    "top_of_page_buttons": ["view"],
}

myst_heading_anchors = 3
suppress_warnings = ["myst.xref_missing", "misc.highlighting_failure"]

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": False,
    "member-order": "bysource",
}

copybutton_prompt_text = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp = True

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
}
