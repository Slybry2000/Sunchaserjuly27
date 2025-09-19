"""Top-level shim package for utils re-exporting Backend.utils.

Forwards attribute access to Backend.utils with no star-imports.
"""

from importlib import import_module as _import_module
from types import ModuleType
from typing import Any

_backend_utils: ModuleType = _import_module("Backend.utils")

# Forward package search to Backend.utils so `import utils.etag` resolves
# to Backend/utils/etag.py at import time.
__path__ = getattr(_backend_utils, "__path__", [])


def __getattr__(name: str) -> Any:  # pragma: no cover - thin shim
    return getattr(_backend_utils, name)


def __dir__() -> list[str]:  # pragma: no cover - thin shim
    return list(getattr(_backend_utils, "__all__", [])) + [
        n for n in dir(_backend_utils) if not n.startswith("_")
    ]


__all__ = getattr(_backend_utils, "__all__", [])
