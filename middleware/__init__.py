"""Top-level shim package for middleware re-exporting Backend.middleware

This allows code that imports `middleware.foo` to resolve to `Backend.middleware.foo`
for tools like mypy and for CI type checking.
"""
from importlib import import_module as _im

_backend_middleware = _im("Backend.middleware")

from Backend.middleware import *  # re-export everything

__all__ = getattr(_backend_middleware, "__all__", [])
