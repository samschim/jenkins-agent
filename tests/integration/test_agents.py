"""Integration tests for LangChain agents."""
import pytest
from langchain_jenkins.agents.supervisor import SupervisorAgent
from langchain_jenkins.agents.build_manager import BuildManagerAgent
from langchain_jenkins.agents.log_analyzer import LogAnalyzerAgent
from langchain_jenkins.agents.pipeline_manager import PipelineManagerAgent
from langchain_jenkins.agents.plugin_manager import PluginManagerAgent
from langchain_jenkins.agents.user_manager import UserManagerAgent

@pytest.fixture
def supervisor():
    """Create a supervisor agent for testing."""
    return SupervisorAgent()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_build_manager(supervisor):
    """Test build manager agent."""
    result = await supervisor.handle_task("Get status of test-job")
    assert result is not None
    assert "status" in result
    assert result["status"] in ["success", "error"]

@pytest.mark.integration
@pytest.mark.asyncio
async def test_log_analyzer(supervisor):
    """Test log analyzer agent."""
    result = await supervisor.handle_task("Analyze logs for test-job")
    assert result is not None
    assert "status" in result
    assert result["status"] in ["success", "error"]

@pytest.mark.integration
@pytest.mark.asyncio
async def test_pipeline_manager(supervisor):
    """Test pipeline manager agent."""
    result = await supervisor.handle_task("Get pipeline status for test-job")
    assert result is not None
    assert "status" in result
    assert result["status"] in ["success", "error"]

@pytest.mark.integration
@pytest.mark.asyncio
async def test_plugin_manager(supervisor):
    """Test plugin manager agent."""
    result = await supervisor.handle_task("List installed plugins")
    assert result is not None
    assert "status" in result
    assert result["status"] in ["success", "error"]

@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_manager(supervisor):
    """Test user manager agent."""
    result = await supervisor.handle_task("List users")
    assert result is not None
    assert "status" in result
    assert result["status"] in ["success", "error"]

@pytest.mark.integration
@pytest.mark.asyncio
async def test_complex_task(supervisor):
    """Test handling of complex tasks."""
    result = await supervisor.handle_complex_task(
        "Check test-job build status and analyze its logs"
    )
    assert result is not None
    assert "status" in result
    assert "results" in result
    assert isinstance(result["results"], dict)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_handling(supervisor):
    """Test error handling in agents."""
    result = await supervisor.handle_task("Get status of nonexistent-job")
    assert result is not None
    assert "status" in result
    assert result["status"] == "error"
    assert "error" in result

@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_coordination(supervisor):
    """Test coordination between agents."""
    result = await supervisor.handle_complex_task(
        "Install git plugin and create a pipeline job"
    )
    assert result is not None
    assert "status" in result
    assert "results" in result
    assert "plugin" in result["results"]
    assert "pipeline" in result["results"]