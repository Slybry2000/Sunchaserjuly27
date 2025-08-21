import hashlib
import json
from decimal import Decimal


def strong_etag(payload_bytes: bytes) -> str:
    """Return a quoted SHA-256 hex digest for given bytes (backwards compatible)."""
    return '"' + hashlib.sha256(payload_bytes).hexdigest() + '"'


def _default_float_converter(o):
    # Decimal is used to ensure consistent string formatting for floats when
    # callers pass numeric types that may differ across runs. Fall back to
    # str() for other unknown types to avoid serialization errors.
    if isinstance(o, Decimal):
        # normalize to a fixed string representation without scientific notation
        return format(o, 'f')
    return str(o)


def strong_etag_for_obj(obj) -> str:
    """Canonicalize a Python object to deterministic JSON bytes and return a quoted SHA-256 ETag.

    Rules:
    - Sort object keys (sort_keys=True)
    - Minify separators (separators=(",", ":"))
    - Use Decimal for precise float formatting where possible
    - Use a stable default serializer for non-standard types
    """
    # Convert floats to Decimal to avoid differences in float repr across runs
    def _convert(o):
        if isinstance(o, float):
            return Decimal(str(o))
        if isinstance(o, dict):
            return {k: _convert(v) for k, v in o.items()}
        if isinstance(o, list):
            return [_convert(v) for v in o]
        return o

    converted = _convert(obj)
    payload = json.dumps(converted, sort_keys=True, separators=(',', ':'), default=_default_float_converter)
    return strong_etag(payload.encode('utf-8'))

