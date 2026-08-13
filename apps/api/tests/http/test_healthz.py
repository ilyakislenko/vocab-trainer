import httpx
import pytest

from vocab_api.main import create_app


@pytest.mark.asyncio
async def test_healthz_returns_ok():
    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
