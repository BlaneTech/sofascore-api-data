"""
Tests pour l'API GOGAinde-Data
"""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_root():
    """Test de la route racine"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Welcome to GOGAinde-Data API"


@pytest.mark.asyncio
async def test_health_check():
    """Test du health check"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_get_leagues():
    """Test de récupération des leagues"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/leagues")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "leagues" in data["data"]


@pytest.mark.asyncio
async def test_get_teams():
    """Test de récupération des équipes"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/teams")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "teams" in data["data"]


@pytest.mark.asyncio
async def test_get_fixtures():
    """Test de récupération des fixtures"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/fixtures")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "fixtures" in data["data"]


@pytest.mark.asyncio
async def test_get_players():
    """Test de récupération des joueurs"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/players")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "players" in data["data"]


@pytest.mark.asyncio
async def test_get_league_not_found():
    """Test de récupération d'une league inexistante"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/leagues/99999")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_team_not_found():
    """Test de récupération d'une équipe inexistante"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/teams/99999")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_fixture_not_found():
    """Test de récupération d'un fixture inexistant"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/fixtures/99999")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_pagination():
    """Test de la pagination"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/teams?page=1&per_page=5")
        assert response.status_code == 200
        data = response.json()
        assert "meta" in data
        assert data["meta"]["page"] == 1
        assert data["meta"]["per_page"] == 5
