import threading
from typing import Dict

_lock = threading.Lock()
_counters: Dict[str, int] = {}

# Optional Prometheus integration (used if prometheus_client is installed)
prometheus_available = False
CONTENT_TYPE_LATEST = 'text/plain; version=0.0.4; charset=utf-8'
_prom_generate_latest = None
_prom_counters = {}
try:
    from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST as _CT

    prometheus_available = True
    CONTENT_TYPE_LATEST = _CT

    def _get_prom_counter(name: str):
        if name not in _prom_counters:
            # use a simple name sanitization: replace invalid chars with _
            cname = name.replace('.', '_').replace('-', '_')
            _prom_counters[name] = Counter(cname, f'Counter for {name}')
        return _prom_counters[name]

    _prom_generate_latest = generate_latest
except Exception:
    prometheus_available = False


def incr(name: str, amount: int = 1) -> None:
    """Increment a named counter by amount (thread-safe).

    If `prometheus_client` is available, increment the Prometheus counter as well.
    """
    with _lock:
        _counters[name] = _counters.get(name, 0) + int(amount)
    if prometheus_available:
        try:
            _get_prom_counter(name).inc(amount)
        except Exception:
            # don't let metrics failures bubble up
            pass


def get_metrics() -> Dict[str, int]:
    with _lock:
        return dict(_counters)


def reset() -> None:
    with _lock:
        _counters.clear()


def prometheus_metrics() -> bytes:
    """Return Prometheus exposition text (bytes). Raises RuntimeError if unavailable."""
    if not prometheus_available or _prom_generate_latest is None:
        raise RuntimeError('prometheus_client not available')
    return _prom_generate_latest()
