"""Top-level shim package for services re-exporting Backend.services

This allows code that imports `services.foo` to resolve to `Backend.services.foo`
for tools like mypy and for CI type checking.
"""
from importlib import import_module as _im

_backend_services = _im("Backend.services")

from Backend.services import *  # re-export everything

__all__ = getattr(_backend_services, "__all__", [])
