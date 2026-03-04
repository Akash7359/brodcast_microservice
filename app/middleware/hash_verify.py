from fastapi import Depends, HTTPException, status
from app.core.security import verify_hash, is_hash_expired
import logging

logger = logging.getLogger(__name__)


def verify_request_hash(payload: dict, incoming_hash: str, timestamp: int) -> None:
    """
    FastAPI dependency to verify HMAC hash and check expiration.
    Raises HTTP 400 if hash is invalid or expired.
    """
    if is_hash_expired(timestamp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request hash has expired.",
        )
    if not verify_hash(payload, incoming_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request hash. Authentication failed.",
        )
