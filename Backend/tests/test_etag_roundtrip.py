import json
from utils.etag import strong_etag_for_obj


def _without_generated_at_or_recommendations(payload: dict) -> dict:
    # Router computes ETag before adding the 'recommendations' alias, so
    # remove both keys to simulate the same canonical input.
    return {k: v for k, v in payload.items() if k not in ("generated_at", "recommendations")}


def test_etag_stable_across_router_roundtrip():
    payload = {
        "query": {"lat": 47.6, "lon": -122.3, "radius": 100},
        "results": [{"id": "PNW_001", "score": 12.34, "distance_mi": 10.1}],
        "version": "v1",
    }

    # ETag computed directly from the Python object (canonicalized)
    etag_direct = strong_etag_for_obj(_without_generated_at_or_recommendations(payload))

    # Simulate router serialization behavior (recommend uses json.dumps(..., default=str, separators=(",",":"), sort_keys=True))
    payload_out = dict(payload)
    payload_out["recommendations"] = payload_out.get("results")
    serialized = json.dumps(payload_out, default=str, separators=(",", ":"), sort_keys=True)
    loaded = json.loads(serialized)

    # Compute ETag on the loaded payload (remove generated_at if present)
    etag_after_roundtrip = strong_etag_for_obj(_without_generated_at_or_recommendations(loaded))

    assert etag_direct == etag_after_roundtrip
