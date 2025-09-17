import sys
from pprint import pprint

photo_id = sys.argv[1] if len(sys.argv) > 1 else None
access_key = sys.argv[2] if len(sys.argv) > 2 else None

if not photo_id or not access_key:
    print("usage: debug_fetch_meta.py <photo_id> <access_key>")
    sys.exit(2)

print("Photo ID:", photo_id)
print("Using access_key:", access_key[:6] + "...")

# Call helper fetch
try:
    from Backend.services import unsplash_integration as ui

    res = ui.fetch_photo_meta(photo_id, access_key, timeout=10.0)
    print("\nResult from fetch_photo_meta():")
    pprint(res)
except Exception as e:
    print("Exception calling fetch_photo_meta:", e)

# Also call Unsplash API directly via requests
try:
    import requests

    url = f"https://api.unsplash.com/photos/{photo_id}"
    headers = {"Authorization": f"Client-ID {access_key}"}
    r = requests.get(url, headers=headers, timeout=10)
    print("\nDirect requests.get status:", r.status_code)
    try:
        j = r.json()
        print("Direct JSON keys:", list(j.keys())[:10])
    except Exception:
        print("Direct response text:", r.text[:500])
except Exception as e:
    print("Exception calling Unsplash directly:", e)
