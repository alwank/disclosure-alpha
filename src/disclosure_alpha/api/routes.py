"""Thin entry: app factory re-export for backward compatibility."""

from disclosure_alpha.api.app_factory import create_app

app = create_app()
