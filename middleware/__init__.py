"""Top-level shim package for middleware re-exporting Backend.middleware.

Forwards attribute access to Backend.middleware.
"""

from importlib import import_module as _import_module
from types import ModuleType
from typing import Any

_backend_middleware: ModuleType = _import_module("Backend.middleware")


def __getattr__(name: str) -> Any:  # pragma: no cover - thin shim
    return getattr(_backend_middleware, name)


def __dir__() -> list[str]:  # pragma: no cover - thin shim
    return list(getattr(_backend_middleware, "__all__", [])) + [
        n for n in dir(_backend_middleware) if not n.startswith("_")
    ]


__all__ = getattr(_backend_middleware, "__all__", [])
