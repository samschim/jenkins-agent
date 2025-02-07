"""Test enhanced supervisor agent functionality."""
import pytest
from langchain_jenkins.agents.supervisor import SupervisorAgent

pytestmark = pytest.mark.asyncio

async def test_embedding_based_routing(mock_jenkins_api, mock_llm):
    """Test that tasks are routed correctly using embeddings."""
    supervisor = SupervisorAgent()
    
    # Test build-related task
    build_result = await supervisor.handle_task(
        "Create a new Jenkins job for building a Python project"
    )
    assert build_result["status"] == "success"
    assert build_result["agent_type"] == "build"
    
    # Test log-related task
    log_result = await supervisor.handle_task(
        "Analyze the build failure and suggest fixes"
    )
    assert log_result["status"] == "success"
    assert log_result["agent_type"] == "log"
    
    # Test pipeline-related task
    pipeline_result = await supervisor.handle_task(
        "Create a new pipeline with build and test stages"
    )
    assert pipeline_result["status"] == "success"
    assert pipeline_result["agent_type"] == "pipeline"
    
    # Test plugin-related task
    plugin_result = await supervisor.handle_task(
        "Install and configure the Git plugin"
    )
    assert plugin_result["status"] == "success"
    assert plugin_result["agent_type"] == "plugin"
    
    # Test user-related task
    user_result = await supervisor.handle_task(
        "Add a new user with admin permissions"
    )
    assert user_result["status"] == "success"
    assert user_result["agent_type"] == "user"

async def test_metrics_collection(mock_jenkins_api, mock_llm):
    """Test metrics collection and insights generation."""
    supervisor = SupervisorAgent()
    result = await supervisor.collect_metrics_and_insights()
    
    assert result["status"] == "success"
    assert "metrics" in result
    assert "insights" in result
    assert "timestamp" in result
    
    # Check metrics structure
    metrics = result["metrics"]
    assert "builds" in metrics
    assert "pipelines" in metrics
    assert "recommendations" in metrics
    
    # Check insights
    insights = result["insights"]
    assert isinstance(insights, str)
    assert len(insights) > 0

async def test_complex_task_handling(mock_jenkins_api, mock_llm):
    """Test handling of complex tasks requiring multiple agents."""
    supervisor = SupervisorAgent()
    
    # Test task requiring build and log analysis
    result = await supervisor.handle_complex_task(
        "Create a new build job and analyze its first build log"
    )
    assert result["status"] == "success"
    assert "build" in result["results"]
    assert "log" in result["results"]
    
    # Test task requiring pipeline and plugin management
    result = await supervisor.handle_complex_task(
        "Create a pipeline and install required plugins"
    )
    assert result["status"] == "success"
    assert "pipeline" in result["results"]
    assert "plugin" in result["results"]

async def test_error_handling(mock_jenkins_api, mock_llm):
    """Test error handling in supervisor agent."""
    supervisor = SupervisorAgent()
    
    # Test with invalid agent type
    result = await supervisor.handle_task(
        "Some task",
        agent_type="invalid_agent"
    )
    assert result["status"] == "error"
    assert "error" in result
    
    # Test with failing task
    result = await supervisor.handle_task(
        "This task will fail"
    )
    assert result["status"] == "error"
    assert "error" in result

async def test_metrics_error_handling(mock_jenkins_api, mock_llm):
    """Test error handling in metrics collection."""
    supervisor = SupervisorAgent()
    
    # Break the metrics collector
    supervisor.metrics_collector = None
    
    result = await supervisor.collect_metrics_and_insights()
    assert result["status"] == "error"
    assert "error" in result