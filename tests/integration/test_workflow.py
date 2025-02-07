"""Integration tests for workflow execution."""
import pytest
from langchain_jenkins.agents.workflow_manager import workflow_manager
from langchain_jenkins.db.mongo_client import mongo_client

@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_workflow(
    mock_jenkins_api,
    mock_llm,
    mock_lm_studio,
    mock_webhook,
    redis_client
):
    """Test complete workflow execution."""
    # Start workflow
    result = await workflow_manager.execute_workflow(
        "Start build for test-job and analyze logs"
    )
    
    assert result["status"] == "success"
    assert len(result["agents"]) > 0
    assert len(result["messages"]) > 0
    
    # Check Redis events
    events = await redis_client.lrange("jenkins_events", 0, -1)
    assert len(events) > 0
    
    # Check MongoDB logs
    logs = await mongo_client.logs.find({}).to_list(None)
    assert len(logs) > 0
    
    # Check agent states
    assert "build_manager" in result["agents"]
    assert result["agents"]["build_manager"]["status"] == "success"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_handling(
    mock_jenkins_api,
    mock_llm,
    mock_lm_studio,
    mock_webhook,
    redis_client
):
    """Test error handling in workflow."""
    # Simulate error
    mock_jenkins_api.build_job = lambda *args: exec('raise Exception("Build failed")')
    
    result = await workflow_manager.execute_workflow(
        "Start build for test-job"
    )
    
    assert result["status"] == "error"
    assert "error" in result
    
    # Check error storage
    errors = await mongo_client.errors.find({}).to_list(None)
    assert len(errors) > 0
    assert errors[0]["error_type"] == "build_failure"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_parallel_workflows(
    mock_jenkins_api,
    mock_llm,
    mock_lm_studio,
    mock_webhook,
    redis_client
):
    """Test parallel workflow execution."""
    # Start multiple workflows
    tasks = [
        workflow_manager.execute_workflow(f"Start build for job-{i}")
        for i in range(3)
    ]
    
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 3
    assert all(r["status"] == "success" for r in results)
    
    # Check task ordering
    events = await redis_client.lrange("jenkins_events", 0, -1)
    assert len(events) == 3

@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_coordination(
    mock_jenkins_api,
    mock_llm,
    mock_lm_studio,
    mock_webhook,
    redis_client
):
    """Test agent coordination."""
    result = await workflow_manager.execute_workflow(
        "Start build for test-job and analyze logs if build fails"
    )
    
    assert result["status"] == "success"
    assert "build_manager" in result["agents"]
    assert "log_analyzer" in result["agents"]
    
    # Check message passing
    assert len(result["messages"]) >= 2
    assert any("build_manager" in m["role"] for m in result["messages"])
    assert any("log_analyzer" in m["role"] for m in result["messages"])

@pytest.mark.integration
@pytest.mark.asyncio
async def test_state_management(
    mock_jenkins_api,
    mock_llm,
    mock_lm_studio,
    mock_webhook,
    redis_client
):
    """Test workflow state management."""
    result = await workflow_manager.execute_workflow(
        "Start build for test-job"
    )
    
    assert result["status"] == "success"
    
    # Check state storage
    state = await redis_client.get(f"workflow:{result['id']}")
    assert state is not None
    
    # Check state cleanup
    await asyncio.sleep(1)  # Wait for cleanup
    state = await redis_client.get(f"workflow:{result['id']}")
    assert state is None