__all__ = ["app"]


def __getattr__(name: str):
    """Avoid constructing the process-wide API while importing app internals."""

    if name == "app":
        from disclosure_alpha.api.routes import app

        return app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
