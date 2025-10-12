import hashlib

def sha256_hash(data: str) -> str:
    """Verilen string için SHA256 hash üretir"""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()
