"""Top-level shim package for models re-exporting Backend.models

This allows code that imports `models.foo` to resolve to `Backend.models.foo`
for tools like mypy and for CI type checking.
"""
from importlib import import_module as _im

_backend_models = _im("Backend.models")

from Backend.models import *  # re-export everything

__all__ = getattr(_backend_models, "__all__", [])
