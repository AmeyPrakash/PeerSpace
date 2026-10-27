"""
PeerSpace Backend Package
"""

__all__ = ["app", "create_app"]

def __getattr__(name: str):
    if name in ("app", "create_app"):
        from backend.app import app, create_app
        return app if name == "app" else create_app
    raise AttributeError(f"module 'backend' has no attribute '{name}'")
