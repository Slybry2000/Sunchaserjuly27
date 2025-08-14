import hashlib
def strong_etag(payload_bytes: bytes) -> str:
    return '"' + hashlib.sha256(payload_bytes).hexdigest() + '"'
