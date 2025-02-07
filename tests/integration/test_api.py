"""Integration tests for API endpoints."""
import pytest
from httpx import AsyncClient

@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_status_endpoint(
    async_client: AsyncClient,
    mock_jenkins_api,
    redis_client
):
    """Test agent status endpoint."""
    response = await async_client.get("/api/agents/status")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    
    agent = data[0]
    assert "name" in agent
    assert "status" in agent
    assert "tasks" in agent
    assert "memory_usage" in agent
    assert "cpu_usage" in agent

@pytest.mark.integration
@pytest.mark.asyncio
async def test_task_history_endpoint(
    async_client: AsyncClient,
    mock_jenkins_api,
    mongo_client
):
    """Test task history endpoint."""
    # Create test task
    await mongo_client.logs.insert_one({
        "build_id": "1",
        "job_name": "test-job",
        "status": "success",
        "timestamp": "2024-02-07T12:00:00Z"
    })
    
    response = await async_client.get("/api/tasks/history")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["build_id"] == "1"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_system_metrics_endpoint(
    async_client: AsyncClient,
    mock_prometheus,
    redis_client
):
    """Test system metrics endpoint."""
    response = await async_client.get("/api/system/metrics")
    assert response.status_code == 200
    
    data = response.json()
    assert "cpu_usage" in data
    assert "memory_usage" in data
    assert "active_tasks" in data
    assert "error_rate" in data

@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_analysis_endpoint(
    async_client: AsyncClient,
    mock_jenkins_api,
    mongo_client
):
    """Test error analysis endpoint."""
    # Create test error
    await mongo_client.errors.insert_one({
        "build_id": "1",
        "job_name": "test-job",
        "error_type": "build_failure",
        "error_message": "Build failed",
        "timestamp": "2024-02-07T12:00:00Z"
    })
    
    response = await async_client.get("/api/errors/analysis")
    assert response.status_code == 200
    
    data = response.json()
    assert "patterns" in data
    assert "correlations" in data
    assert "distribution" in data

@pytest.mark.integration
@pytest.mark.asyncio
async def test_task_management_endpoints(
    async_client: AsyncClient,
    mock_jenkins_api,
    redis_client
):
    """Test task management endpoints."""
    # Start task
    response = await async_client.post(
        "/api/tasks",
        json={
            "description": "Start build for test-job",
            "agent": "build_manager"
        }
    )
    assert response.status_code == 200
    task_id = response.json()["id"]
    
    # Get task status
    response = await async_client.get(f"/api/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    
    # Stop task
    response = await async_client.post(f"/api/tasks/{task_id}/stop")
    assert response.status_code == 200
    assert response.json()["status"] == "stopped"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_management_endpoints(
    async_client: AsyncClient,
    mock_jenkins_api,
    redis_client
):
    """Test agent management endpoints."""
    # Get agent logs
    response = await async_client.get("/api/agents/build_manager/logs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    
    # Update agent config
    response = await async_client.put(
        "/api/agents/build_manager/config",
        json={"max_tasks": 5}
    )
    assert response.status_code == 200
    
    # Get agent metrics
    response = await async_client.get("/api/agents/build_manager/metrics")
    assert response.status_code == 200
    assert "cpu_usage" in response.json()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_webhook_endpoints(
    async_client: AsyncClient,
    mock_webhook,
    redis_client
):
    """Test webhook endpoints."""
    # Send webhook
    response = await async_client.post(
        "/webhook",
        json={
            "build": {
                "full_url": "http://jenkins/job/test-job/1/",
                "number": 1,
                "status": "SUCCESS",
                "phase": "COMPLETED"
            }
        }
    )
    assert response.status_code == 200
    
    # Check event storage
    events = await redis_client.lrange("jenkins_events", 0, -1)
    assert len(events) == 1