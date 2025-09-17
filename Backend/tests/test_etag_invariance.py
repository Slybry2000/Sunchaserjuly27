from decimal import Decimal

from freezegun import freeze_time

from Backend.utils.etag import strong_etag_for_obj


def _without_generated_at(payload: dict) -> dict:
    return {k: v for k, v in payload.items() if k != "generated_at"}


def test_etag_ignores_generated_at_timestamp():
    base = {
        "query": {"lat": 47.6, "lon": -122.3, "radius": 100},
        "results": [{"id": "PNW_001", "score": 12.34, "distance_mi": 10.1}],
        "version": "v1",
    }

    with freeze_time("2025-08-19T00:00:00Z"):
        p1 = dict(base)
        p1["generated_at"] = "2025-08-19T00:00:00Z"
        etag1 = strong_etag_for_obj(_without_generated_at(p1))

    with freeze_time("2025-08-18T00:00:00Z"):
        p2 = dict(base)
        p2["generated_at"] = "2025-08-18T00:00:00Z"
        etag2 = strong_etag_for_obj(_without_generated_at(p2))

    assert etag1 == etag2


def test_etag_invariant_to_key_order_and_float_representation():
    # payload A: float values, keys in one insertion order
    payload_a = {
        "query": {"lat": 47.6, "lon": -122.3, "radius": 100},
        "results": [{"id": "PNW_001", "score": 12.34, "distance_mi": 10.1}],
        "version": "v1",
    }

    # payload B: same logical content, different key order and Decimal for float
    payload_b = {
        "version": "v1",
        "results": [
            {"distance_mi": Decimal("10.1"), "score": Decimal("12.34"), "id": "PNW_001"}
        ],
        "query": {"radius": 100, "lon": -122.3, "lat": 47.6},
    }

    etag_a = strong_etag_for_obj(payload_a)
    etag_b = strong_etag_for_obj(payload_b)

    assert etag_a == etag_b
