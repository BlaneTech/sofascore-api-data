import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.main import app


@pytest.mark.asyncio
async def test_get_fixtures():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch('app.auth.verify_api_key') as mock_auth:
            mock_auth.return_value = AsyncMock()
            
            response = await client.get("/fixtures", headers={"X-API-Key": "test_key"})
            
            assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_fixture_by_id():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch('app.auth.verify_api_key') as mock_auth:
            mock_auth.return_value = AsyncMock()
            
            response = await client.get("/fixtures/1", headers={"X-API-Key": "test_key"})
            
            assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_get_teams():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch('app.auth.verify_api_key') as mock_auth:
            mock_auth.return_value = AsyncMock()
            
            response = await client.get("/teams", headers={"X-API-Key": "test_key"})
            
            assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_players():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch('app.auth.verify_api_key') as mock_auth:
            mock_auth.return_value = AsyncMock()
            
            response = await client.get("/players?team_id=1", headers={"X-API-Key": "test_key"})
            
            assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_standings():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch('app.auth.verify_api_key') as mock_auth:
            mock_auth.return_value = AsyncMock()
            
            response = await client.get("/standings?season_id=1", headers={"X-API-Key": "test_key"})
            
            assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_match_statistics():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch('app.auth.verify_api_key') as mock_auth:
            mock_auth.return_value = AsyncMock()
            
            response = await client.get("/statistics/match/1", headers={"X-API-Key": "test_key"})
            
            assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_fixture_filters():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch('app.auth.verify_api_key') as mock_auth:
            mock_auth.return_value = AsyncMock()
            
            response = await client.get(
                "/fixtures?status=finished&page=1&per_page=10",
                headers={"X-API-Key": "test_key"}
            )
            
            assert response.status_code == 200


@pytest.mark.asyncio
async def test_invalid_fixture_id():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch('app.auth.verify_api_key') as mock_auth:
            mock_auth.return_value = AsyncMock()
            
            response = await client.get("/fixtures/999999", headers={"X-API-Key": "test_key"})
            
            assert response.status_code == 404