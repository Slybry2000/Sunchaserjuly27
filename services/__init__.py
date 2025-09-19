"""Top-level shim package for services re-exporting Backend.services.

This module forwards attribute access to `Backend.services` without using
``from ... import *`` so linters (ruff) won't complain. It preserves runtime
behavior for tests and tooling that import ``services.*``.
"""

from importlib import import_module as _import_module
from types import ModuleType
from typing import Any

_backend_services: ModuleType = _import_module("Backend.services")


def __getattr__(name: str) -> Any:  # pragma: no cover - thin shim
    return getattr(_backend_services, name)


def __dir__() -> list[str]:  # pragma: no cover - thin shim
    return list(getattr(_backend_services, "__all__", [])) + [
        n for n in dir(_backend_services) if not n.startswith("_")
    ]


__all__ = getattr(_backend_services, "__all__", [])
