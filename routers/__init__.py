"""Top-level shim package for routers re-exporting Backend.routers

This allows code that imports `routers.foo` to resolve to `Backend.routers.foo`
for tools like mypy and for CI type checking.
"""
from importlib import import_module as _im

_backend_routers = _im("Backend.routers")

from Backend.routers import *  # re-export everything

__all__ = getattr(_backend_routers, "__all__", [])
