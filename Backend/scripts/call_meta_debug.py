import json

import requests

url = "http://127.0.0.1:8000/internal/photos/meta?photo_id=eOLpJytrbsQ&debug=1"
headers = {"X-Debug-Unsplash-Key": "iqEqFxbDVbBPJgrHR7JJibdKnG9sFJhbpw3I-YjsT1w"}
print("Calling", url)
r = requests.get(url, headers=headers, timeout=15)
print("status", r.status_code)
try:
    print(json.dumps(r.json(), indent=2))
except Exception:
    print(r.text)
