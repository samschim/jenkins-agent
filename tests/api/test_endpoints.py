"""API endpoint tests."""
import pytest
from httpx import AsyncClient
from fastapi import status

pytestmark = [pytest.mark.api, pytest.mark.asyncio]

async def test_health_check(async_client: AsyncClient):
    """Test health check endpoint."""
    response = await async_client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "healthy"}

async def test_list_agents(async_client: AsyncClient):
    """Test listing available agents."""
    # Get token first
    token_response = await async_client.post(
        "/token",
        data={"username": "admin", "password": "password"}
    )
    assert token_response.status_code == status.HTTP_200_OK
    token = token_response.json()["access_token"]

    # List agents
    response = await async_client.get(
        "/agents",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "agents" in data
    assert len(data["agents"]) > 0
    assert all("type" in agent for agent in data["agents"])
    assert all("description" in agent for agent in data["agents"])

async def test_execute_task(async_client: AsyncClient):
    """Test task execution endpoint."""
    # Get token first
    token_response = await async_client.post(
        "/token",
        data={"username": "admin", "password": "password"}
    )
    assert token_response.status_code == status.HTTP_200_OK
    token = token_response.json()["access_token"]

    # Execute task
    response = await async_client.post(
        "/task",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "task": "Analyze build log",
            "agent_type": "log"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "status" in data
    assert "result" in data
    assert "task" in data
    assert "agent_type" in data

async def test_analyze_log(async_client: AsyncClient):
    """Test log analysis endpoint."""
    # Get token first
    token_response = await async_client.post(
        "/token",
        data={"username": "admin", "password": "password"}
    )
    assert token_response.status_code == status.HTTP_200_OK
    token = token_response.json()["access_token"]

    # Analyze log
    response = await async_client.post(
        "/api/logs/analyze",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "log": """
            [INFO] Building project...
            [ERROR] Failed to compile: missing dependency org.example:library:1.0.0
            [ERROR] Could not resolve dependencies
            [INFO] BUILD FAILURE
            """
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "status" in data
    assert "result" in data

async def test_unauthorized_access(async_client: AsyncClient):
    """Test unauthorized access to protected endpoints."""
    # Try to access protected endpoint without token
    response = await async_client.get("/agents")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Try to access with invalid token
    response = await async_client.get(
        "/agents",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

async def test_invalid_task(async_client: AsyncClient):
    """Test handling of invalid task requests."""
    # Get token first
    token_response = await async_client.post(
        "/token",
        data={"username": "admin", "password": "password"}
    )
    assert token_response.status_code == status.HTTP_200_OK
    token = token_response.json()["access_token"]

    # Try to execute task with invalid agent type
    response = await async_client.post(
        "/task",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "task": "Analyze build log",
            "agent_type": "invalid_agent"
        }
    )
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR