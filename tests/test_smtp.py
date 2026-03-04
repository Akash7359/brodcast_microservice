import pytest
import time
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from app.main import app
from app.core.security import generate_hash, verify_hash, is_hash_expired


# ── Security unit tests ───────────────────────────────────────────────────────

def test_generate_hash_deterministic():
    payload = {"project_id": 1, "category_type_id": 2, "broadcast_channel_type": 1}
    h1 = generate_hash(payload)
    h2 = generate_hash(payload)
    assert h1 == h2


def test_verify_hash_valid():
    payload = {"project_id": 1, "category_type_id": 2, "broadcast_channel_type": 1}
    h = generate_hash(payload)
    assert verify_hash(payload, h) is True


def test_verify_hash_tampered():
    payload = {"project_id": 1, "category_type_id": 2, "broadcast_channel_type": 1}
    h = generate_hash(payload)
    payload["project_id"] = 99
    assert verify_hash(payload, h) is False


def test_hash_not_expired():
    assert is_hash_expired(int(time.time())) is False


def test_hash_expired():
    old_ts = int(time.time()) - 600
    assert is_hash_expired(old_ts) is True


# ── Integration tests ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/test")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_generate_hash_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/generate-hash",
            json={"payload": {"project_id": 1, "category_type_id": 1}},
        )
    assert response.status_code == 200
    assert "hash" in response.json()


@pytest.mark.asyncio
async def test_send_smtp_invalid_hash():
    payload = {
        "project_id": 1,
        "category_type_id": 1,
        "broadcast_channel_type": 1,
        "to_email": "test@example.com",
        "hash": "badhash",
        "timestamp": int(time.time()),
        "data": {},
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/v1/send-smtp", json=payload)
    assert response.status_code == 400
