import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base, get_db
from app.main import app

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)

# Create test session factory
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database dependency override."""

    def override_get_db():
        return db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPassword123!",
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False,
    }


@pytest.fixture
def sample_pelanggan_data():
    """Sample pelanggan data for testing."""
    return {
        "nama": "Test Customer",
        "email": "customer@example.com",
        "no_telepon": "+62812345678",
        "alamat": "Test Address 123",
        "kode_pos": "12345",
        "kota": "Test City",
        "provinsi": "Test Province",
    }


@pytest.fixture
def sample_paket_layanan_data():
    """Sample paket layanan data for testing."""
    return {
        "nama": "Test Package",
        "deskripsi": "Test package description",
        "harga": 150000,
        "kecepatan": "100 Mbps",
        "tipe": "Fiber",
        "is_active": True,
    }


@pytest.fixture
def sample_invoice_data():
    """Sample invoice data for testing."""
    return {
        "nomor_invoice": "INV-TEST-001",
        "jumlah_tagihan": 150000,
        "tanggal_jatuh_tempo": "2024-12-31",
        "status": "unpaid",
        "deskripsi": "Test invoice description",
    }


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, sample_user_data: dict) -> dict:
    """Create authenticated user and return auth headers."""
    # Create user
    await client.post("/users/", json=sample_user_data)

    # Login to get token
    login_data = {"username": sample_user_data["email"], "password": sample_user_data["password"]}
    response = await client.post("/users/token", data=login_data)

    assert response.status_code == 200
    token_data = response.json()
    access_token = token_data["access_token"]

    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def auth_headers_admin(client: AsyncClient) -> dict:
    """Create admin user and return auth headers."""
    admin_data = {
        "email": "admin@example.com",
        "username": "admin",
        "password": "AdminPassword123!",
        "full_name": "Admin User",
        "is_active": True,
        "is_superuser": True,
    }

    # Create admin user
    await client.post("/users/", json=admin_data)

    # Login to get token
    login_data = {"username": admin_data["email"], "password": admin_data["password"]}
    response = await client.post("/users/token", data=login_data)

    assert response.status_code == 200
    token_data = response.json()
    access_token = token_data["access_token"]

    return {"Authorization": f"Bearer {access_token}"}


# Mock fixtures for external services
@pytest.fixture
def mock_xendit_service():
    """Mock Xendit service for testing."""
    from unittest.mock import Mock, patch

    with patch("app.services.xendit_service.XenditService") as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_mikrotik_service():
    """Mock Mikrotik service for testing."""
    from unittest.mock import Mock, patch

    with patch("app.services.mikrotik_service.MikrotikService") as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_email_service():
    """Mock email service for testing."""
    from unittest.mock import Mock, patch

    with patch("app.services.email_service.EmailService") as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance
