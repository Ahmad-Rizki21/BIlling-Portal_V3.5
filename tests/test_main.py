import pytest
from httpx import AsyncClient


@pytest.mark.unit
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


@pytest.mark.unit
async def test_health_check(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.unit
async def test_docs_endpoint(client: AsyncClient):
    """Test API documentation endpoint."""
    response = await client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.unit
async def test_openapi_endpoint(client: AsyncClient):
    """Test OpenAPI schema endpoint."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data


@pytest.mark.unit
async def test_nonexistent_endpoint(client: AsyncClient):
    """Test 404 for nonexistent endpoint."""
    response = await client.get("/nonexistent")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@pytest.mark.unit
async def test_cors_headers(client: AsyncClient):
    """Test CORS headers."""
    response = await client.options("/")
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


@pytest.mark.integration
async def test_database_connection(db_session):
    """Test database connection."""
    # Simple test to verify database is accessible
    from app.models.user import User

    # This should not raise an exception
    result = await db_session.execute("SELECT 1")
    assert result.scalar() == 1
