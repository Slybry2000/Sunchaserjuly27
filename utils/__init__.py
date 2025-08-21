"""Top-level shim package for utils re-exporting Backend.utils

This allows code that imports `utils.foo` to resolve to `Backend.utils.foo`
for tools like mypy and for CI type checking.
"""
from importlib import import_module as _im

_backend_utils = _im("Backend.utils")

from Backend.utils import *  # re-export everything

__all__ = getattr(_backend_utils, "__all__", [])
