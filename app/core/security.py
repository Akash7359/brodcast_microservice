import hashlib
import hmac
import time
from urllib.parse import urlencode
from fastapi import HTTPException, status
from app.core.config import settings

EXCLUDED_FIELDS = {"hash", "token", "timestamp_skip"}


def generate_hash(payload: dict) -> str:
    """Sort payload keys, build query string, compute HMAC-SHA256."""
    filtered = {k: v for k, v in payload.items() if k not in EXCLUDED_FIELDS}
    sorted_payload = dict(sorted(filtered.items()))
    query_string = urlencode(sorted_payload)
    signature = hmac.new(
        settings.SECRET_KEY_HASH.encode(),
        query_string.encode(),
        hashlib.sha256,
    ).hexdigest()
    return signature


def verify_hash(payload: dict, incoming_hash: str) -> bool:
    """Re-compute hash and compare securely."""
    expected = generate_hash(payload)
    return hmac.compare_digest(expected, incoming_hash)


def verify_hash_or_raise(payload: dict, incoming_hash: str) -> None:
    if not verify_hash(payload, incoming_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request hash. Authentication failed.",
        )


def is_hash_expired(request_timestamp: int) -> bool:
    """Check if the hash has exceeded its expiration window."""
    return (time.time() - request_timestamp) > settings.HASH_EXPIRATION_TIME
