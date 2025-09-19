"""Top-level shim package for routers re-exporting Backend.routers.

Forwards attribute access to Backend without star imports.
"""

from importlib import import_module as _import_module
from types import ModuleType
from typing import Any

_backend_routers: ModuleType = _import_module("Backend.routers")


def __getattr__(name: str) -> Any:  # pragma: no cover - thin shim
    return getattr(_backend_routers, name)


def __dir__() -> list[str]:  # pragma: no cover - thin shim
    return list(getattr(_backend_routers, "__all__", [])) + [
        n for n in dir(_backend_routers) if not n.startswith("_")
    ]


__all__ = getattr(_backend_routers, "__all__", [])
