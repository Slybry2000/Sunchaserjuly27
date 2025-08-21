"""Top-level main shim re-exporting Backend.main as a module alias.

Avoid star-imports so linters won't fail; tests importing `main` can still
access attributes via `main.<name>`.
"""
from importlib import import_module as _import_module

_backend_main = _import_module("Backend.main")

__all__ = [n for n in dir(_backend_main) if not n.startswith("_")]

def __getattr__(name: str):  # pragma: no cover - thin shim
	return getattr(_backend_main, name)
