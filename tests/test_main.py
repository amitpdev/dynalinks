import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db_pg import get_db_instance, PostgresDB
from app.config import settings
from datetime import datetime

# Mock database for testing
class MockPostgresDB(PostgresDB):
    _data = {}

    def __init__(self):
        # Override the __init__ to prevent it from trying to build a DSN
        self.pool = None

    async def connect(self):
        # Mock connection
        self._data = {}

    async def disconnect(self):
        # Mock disconnection
        self._data = {}

    async def fetch(self, query, *args):
        if "SELECT * FROM dynamic_links" in query:
            return list(self._data.values())
        return []

    async def fetchrow(self, query, *args):
        s_query = query.strip()

        if s_query.startswith("SELECT") and "WHERE short_code = $1" in s_query:
            return self._data.get(args[0])

        if s_query.startswith("INSERT"):
            short_code = args[0]
            link_data = {
                "id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
                "short_code": short_code,
                "short_url": f"http://test/{short_code}",
                "fallback_url": str(args[3]).rstrip('/'),
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            self._data[short_code] = link_data
            return link_data

        if s_query.startswith("UPDATE"):
            short_code = args[-1]
            if short_code in self._data:
                if "is_active = FALSE" in s_query:
                    self._data[short_code]['is_active'] = False
                return self._data[short_code]

        return None

    async def execute(self, query, *args):
        pass


# Create a single mock db instance to be used by the app and tests
mock_db = MockPostgresDB()

# Override the get_db_instance dependency
async def override_get_db_instance():
    return mock_db

app.dependency_overrides[get_db_instance] = override_get_db_instance

@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="module")
async def client():
    # Reset mock db for each test module
    await mock_db.connect()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.mark.anyio
async def test_create_link(client: AsyncClient):
    response = await client.post("/api/v1/links/", json={"fallback_url": "https://example.com"})
    assert response.status_code == 200
    data = response.json()
    assert "short_url" in data
    assert len(data["short_code"]) == 7

@pytest.mark.anyio
async def test_create_and_get_link(client: AsyncClient):
    # Create a link
    create_response = await client.post("/api/v1/links/?custom_code=testget", json={"fallback_url": "https://get-example.com"})
    assert create_response.status_code == 200
    created_data = create_response.json()
    short_code = created_data["short_code"]

    # Get the link
    get_response = await client.get(f"/api/v1/links/{short_code}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["fallback_url"] == "https://get-example.com"
    assert get_data["short_code"] == short_code

@pytest.mark.anyio
async def test_delete_link(client: AsyncClient):
    # Create a link
    create_response = await client.post("/api/v1/links/?custom_code=testdelete", json={"fallback_url": "https://delete-example.com"})
    assert create_response.status_code == 200
    short_code = create_response.json()["short_code"]

    # Delete the link
    delete_response = await client.delete(f"/api/v1/links/{short_code}")
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Dynamic link deactivated successfully"

    # Verify it's inactive (by trying to get it, assuming get only returns active)
    # The current get implementation does not check for active status, so this will pass.
    # To properly test, the get logic should be updated or we check the mock db state.
    db = await override_get_db_instance()
    link = await db.fetchrow("SELECT * FROM dynamic_links WHERE short_code = $1", short_code)
    assert link is not None
    assert not link['is_active']


@pytest.mark.anyio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
