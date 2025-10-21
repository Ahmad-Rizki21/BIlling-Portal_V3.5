import pytest
from httpx import AsyncClient


@pytest.mark.unit
async def test_create_user(client: AsyncClient, sample_user_data: dict):
    """Test user creation."""
    response = await client.post("/users/", json=sample_user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == sample_user_data["email"]
    assert data["username"] == sample_user_data["username"]
    assert "id" in data
    assert "password" not in data  # Password should not be returned


@pytest.mark.unit
async def test_create_duplicate_user(client: AsyncClient, sample_user_data: dict):
    """Test creating duplicate user should fail."""
    # Create first user
    await client.post("/users/", json=sample_user_data)

    # Try to create duplicate
    response = await client.post("/users/", json=sample_user_data)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


@pytest.mark.unit
async def test_create_user_invalid_email(client: AsyncClient):
    """Test user creation with invalid email."""
    invalid_data = {"email": "invalid-email", "username": "testuser", "password": "TestPassword123!"}
    response = await client.post("/users/", json=invalid_data)
    assert response.status_code == 422


@pytest.mark.auth
async def test_login_success(client: AsyncClient, sample_user_data: dict):
    """Test successful login."""
    # Create user first
    await client.post("/users/", json=sample_user_data)

    # Login
    login_data = {"username": sample_user_data["email"], "password": sample_user_data["password"]}
    response = await client.post("/users/token", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.auth
async def test_login_invalid_credentials(client: AsyncClient):
    """Test login with invalid credentials."""
    login_data = {"username": "nonexistent@example.com", "password": "wrongpassword"}
    response = await client.post("/users/token", data=login_data)
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.auth
async def test_get_current_user(client: AsyncClient, auth_headers: dict, sample_user_data: dict):
    """Test getting current user info."""
    response = await client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == sample_user_data["email"]
    assert data["username"] == sample_user_data["username"]


@pytest.mark.auth
async def test_get_current_user_invalid_token(client: AsyncClient):
    """Test getting current user with invalid token."""
    headers = {"Authorization": "Bearer invalid_token"}
    response = await client.get("/users/me", headers=headers)
    assert response.status_code == 401


@pytest.mark.auth
async def test_get_current_user_no_token(client: AsyncClient):
    """Test getting current user without token."""
    response = await client.get("/users/me")
    assert response.status_code == 401


@pytest.mark.unit
async def test_user_validation_weak_password(client: AsyncClient):
    """Test user creation with weak password."""
    weak_password_data = {"email": "test@example.com", "username": "testuser", "password": "123"}  # Too short
    response = await client.post("/users/", json=weak_password_data)
    assert response.status_code == 422


@pytest.mark.api
async def test_users_pagination(client: AsyncClient, auth_headers: dict):
    """Test users endpoint with pagination."""
    response = await client.get("/users/?skip=0&limit=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
