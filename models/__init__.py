"""Top-level shim package for models re-exporting Backend.models.

Attribute access is forwarded to the Backend package; avoids star-imports.
"""

from importlib import import_module as _import_module
from types import ModuleType
from typing import Any

_backend_models: ModuleType = _import_module("Backend.models")


def __getattr__(name: str) -> Any:  # pragma: no cover - thin shim
    return getattr(_backend_models, name)


def __dir__() -> list[str]:  # pragma: no cover - thin shim
    return list(getattr(_backend_models, "__all__", [])) + [
        n for n in dir(_backend_models) if not n.startswith("_")
    ]


__all__ = getattr(_backend_models, "__all__", [])
