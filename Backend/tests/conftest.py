import os
import importlib
import pytest

# Explicitly import pytest_asyncio to guarantee the plugin is registered
# in environments where pytest's plugin discovery may not run early enough.
try:
    import pytest_asyncio  # type: ignore
except Exception:
    # best-effort: if import fails, plugin may still be available via entrypoints
    pass

# Rely on the installed pytest-asyncio package and root-level pytest.ini
# (asyncio_mode = auto) to run plain `async def` tests. Defining
# `pytest_plugins` in a non-top-level conftest is deprecated and breaks
# collection under pytest >=8.4.


@pytest.fixture(scope="session", autouse=True)
def enable_sync_cache_refresh():
    """Ensure tests run with deterministic cache refresh behavior by enabling
    CACHE_REFRESH_SYNC for the test session. This mirrors CI behavior and
    prevents flaky background refresh races during unit tests.
    """
    prev = os.environ.get("CACHE_REFRESH_SYNC")
    os.environ["CACHE_REFRESH_SYNC"] = "true"

    # If the cache module was already imported, reload it so module-level
    # SYNC_REFRESH reads the updated env var.
    try:
        import utils.cache_inproc as _cache_inproc
        importlib.reload(_cache_inproc)
    except Exception:
        # best-effort: tests that import the module later will pick up the env var
        pass

    yield

    # Teardown: restore previous env var state
    if prev is None:
        os.environ.pop("CACHE_REFRESH_SYNC", None)
    else:
        os.environ["CACHE_REFRESH_SYNC"] = prev
