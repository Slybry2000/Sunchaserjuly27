import json
from Backend.utils.etag import strong_etag_for_obj


def _without_generated_at(payload: dict) -> dict:
    return {k: v for k, v in payload.items() if k != "generated_at"}


payload = {
    "query": {"lat": 47.6, "lon": -122.3, "radius": 100},
    "results": [{"id": "PNW_001", "score": 12.34, "distance_mi": 10.1}],
    "version": "v1",
}

etag_direct = strong_etag_for_obj(_without_generated_at(payload))

payload_out = dict(payload)
# payload_out.get("results") may be None in some cases; this is a small debug script.
payload_out["recommendations"] = payload_out.get("results")  # type: ignore
serialized = json.dumps(payload_out, default=str, separators=(",", ":"), sort_keys=True)
loaded = json.loads(serialized)

etag_after_roundtrip = strong_etag_for_obj(_without_generated_at(loaded))

print("direct canonical JSON:")
print(
    json.dumps(
        _without_generated_at(payload),
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
)
print("\nafter roundtrip JSON:")
print(
    json.dumps(
        _without_generated_at(loaded),
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
)
print("\netag_direct=", etag_direct)
print("etag_after_roundtrip=", etag_after_roundtrip)
