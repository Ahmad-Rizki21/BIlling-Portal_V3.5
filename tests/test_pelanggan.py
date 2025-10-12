import pytest
from httpx import AsyncClient


@pytest.mark.pelanggan
async def test_create_pelanggan(client: AsyncClient, auth_headers: dict, sample_pelanggan_data: dict):
    """Test creating a new pelanggan."""
    response = await client.post("/pelanggan/", json=sample_pelanggan_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["nama"] == sample_pelanggan_data["nama"]
    assert data["email"] == sample_pelanggan_data["email"]
    assert "id" in data


@pytest.mark.pelanggan
async def test_get_pelanggan_list(client: AsyncClient, auth_headers: dict):
    """Test getting list of pelanggan."""
    response = await client.get("/pelanggan/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.pelanggan
async def test_get_pelanggan_by_id(client: AsyncClient, auth_headers: dict, sample_pelanggan_data: dict):
    """Test getting pelanggan by ID."""
    # Create pelanggan first
    create_response = await client.post("/pelanggan/", json=sample_pelanggan_data, headers=auth_headers)
    pelanggan_id = create_response.json()["id"]

    # Get pelanggan by ID
    response = await client.get(f"/pelanggan/{pelanggan_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == pelanggan_id
    assert data["nama"] == sample_pelanggan_data["nama"]


@pytest.mark.pelanggan
async def test_update_pelanggan(client: AsyncClient, auth_headers: dict, sample_pelanggan_data: dict):
    """Test updating pelanggan information."""
    # Create pelanggan first
    create_response = await client.post("/pelanggan/", json=sample_pelanggan_data, headers=auth_headers)
    pelanggan_id = create_response.json()["id"]

    # Update pelanggan
    update_data = {"nama": "Updated Customer Name"}
    response = await client.put(f"/pelanggan/{pelanggan_id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["nama"] == "Updated Customer Name"


@pytest.mark.pelanggan
async def test_delete_pelanggan(client: AsyncClient, auth_headers: dict, sample_pelanggan_data: dict):
    """Test deleting pelanggan."""
    # Create pelanggan first
    create_response = await client.post("/pelanggan/", json=sample_pelanggan_data, headers=auth_headers)
    pelanggan_id = create_response.json()["id"]

    # Delete pelanggan
    response = await client.delete(f"/pelanggan/{pelanggan_id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify pelanggan is deleted
    get_response = await client.get(f"/pelanggan/{pelanggan_id}", headers=auth_headers)
    assert get_response.status_code == 404


@pytest.mark.pelanggan
async def test_create_pelanggan_invalid_data(client: AsyncClient, auth_headers: dict):
    """Test creating pelanggan with invalid data."""
    invalid_data = {"nama": "", "email": "invalid-email", "no_telepon": ""}  # Empty name  # Invalid email  # Empty phone
    response = await client.post("/pelanggan/", json=invalid_data, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.pelanggan
async def test_get_nonexistent_pelanggan(client: AsyncClient, auth_headers: dict):
    """Test getting non-existent pelanggan."""
    response = await client.get("/pelanggan/99999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.pelanggan
async def test_pelanggan_search(client: AsyncClient, auth_headers: dict, sample_pelanggan_data: dict):
    """Test searching pelanggan."""
    # Create pelanggan first
    await client.post("/pelanggan/", json=sample_pelanggan_data, headers=auth_headers)

    # Search pelanggan
    response = await client.get(f"/pelanggan/?search={sample_pelanggan_data['nama']}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any(p["nama"] == sample_pelanggan_data["nama"] for p in data)


@pytest.mark.pelanggan
async def test_create_pelanggan_unauthorized(client: AsyncClient, sample_pelanggan_data: dict):
    """Test creating pelanggan without authentication."""
    response = await client.post("/pelanggan/", json=sample_pelanggan_data)
    assert response.status_code == 401
