"""Agent functionality tests."""
import pytest
from langchain_jenkins.agents.supervisor import SupervisorAgent
from langchain_jenkins.agents.enhanced_build_manager import EnhancedBuildManager
from langchain_jenkins.agents.enhanced_log_analyzer import EnhancedLogAnalyzer
from langchain_jenkins.agents.enhanced_pipeline_manager import EnhancedPipelineManager
from langchain_jenkins.agents.enhanced_plugin_manager import EnhancedPluginManager

pytestmark = [pytest.mark.agent, pytest.mark.asyncio]

@pytest.fixture
async def supervisor(mock_jenkins_api, mock_llm):
    """Create supervisor agent."""
    return SupervisorAgent()

@pytest.fixture
async def build_manager(mock_jenkins_api, mock_llm):
    """Create build manager agent."""
    return EnhancedBuildManager()

@pytest.fixture
async def log_analyzer(mock_jenkins_api, mock_llm):
    """Create log analyzer agent."""
    return EnhancedLogAnalyzer()

@pytest.fixture
async def pipeline_manager(mock_jenkins_api, mock_llm):
    """Create pipeline manager agent."""
    return EnhancedPipelineManager()

@pytest.fixture
async def plugin_manager(mock_jenkins_api, mock_llm):
    """Create plugin manager agent."""
    return EnhancedPluginManager()

async def test_supervisor_task_routing(supervisor):
    """Test supervisor's task routing capabilities."""
    # Test build task
    build_result = await supervisor.handle_task(
        "Create a new build job named 'test-job'",
        agent_type="build"
    )
    assert build_result["status"] == "success"
    assert "job_name" in build_result
    
    # Test log analysis task
    log_result = await supervisor.handle_task(
        "Analyze this build log: [ERROR] Build failed",
        agent_type="log"
    )
    assert log_result["status"] == "success"
    assert "analysis" in log_result
    
    # Test pipeline task
    pipeline_result = await supervisor.handle_task(
        "Create a new pipeline for Java project",
        agent_type="pipeline"
    )
    assert pipeline_result["status"] == "success"
    assert "pipeline" in pipeline_result
    
    # Test plugin task
    plugin_result = await supervisor.handle_task(
        "Install git plugin",
        agent_type="plugin"
    )
    assert plugin_result["status"] == "success"
    assert "plugin" in plugin_result

async def test_build_manager_functionality(build_manager):
    """Test build manager agent functionality."""
    # Test creating build job
    create_result = await build_manager.handle_task(
        "Create a new Maven build job"
    )
    assert create_result["status"] == "success"
    assert "job_name" in create_result
    
    # Test configuring build job
    config_result = await build_manager.handle_task(
        f"Configure job {create_result['job_name']} to use JDK 11"
    )
    assert config_result["status"] == "success"
    assert "configuration" in config_result
    
    # Test build execution
    build_result = await build_manager.handle_task(
        f"Build job {create_result['job_name']}"
    )
    assert build_result["status"] == "success"
    assert "build_number" in build_result

async def test_log_analyzer_functionality(log_analyzer):
    """Test log analyzer agent functionality."""
    log = """
    [INFO] Building project...
    [ERROR] Failed to compile: missing dependency org.example:library:1.0.0
    [ERROR] Could not resolve dependencies
    [INFO] BUILD FAILURE
    """
    
    # Test log analysis
    analysis_result = await log_analyzer.handle_task(
        f"Analyze this build log: {log}"
    )
    assert analysis_result["status"] == "success"
    assert "analysis" in analysis_result["result"]
    assert "errors" in analysis_result["result"]["analysis"]
    assert "recommendations" in analysis_result["result"]["analysis"]

async def test_pipeline_manager_functionality(pipeline_manager):
    """Test pipeline manager agent functionality."""
    # Test creating pipeline
    create_result = await pipeline_manager.handle_task(
        "Create a new pipeline for Java project with build and test stages"
    )
    assert create_result["status"] == "success"
    assert "pipeline" in create_result["result"]
    
    # Test validating pipeline
    validate_result = await pipeline_manager.handle_task(
        f"Validate this pipeline: {create_result['result']['pipeline']}"
    )
    assert validate_result["status"] == "success"
    assert "validation" in validate_result["result"]
    
    # Test optimizing pipeline
    optimize_result = await pipeline_manager.handle_task(
        f"Optimize this pipeline: {create_result['result']['pipeline']}"
    )
    assert optimize_result["status"] == "success"
    assert "optimizations" in optimize_result["result"]

async def test_plugin_manager_functionality(plugin_manager):
    """Test plugin manager agent functionality."""
    # Test installing plugin
    install_result = await plugin_manager.handle_task(
        "Install git plugin"
    )
    assert install_result["status"] == "success"
    assert "plugin" in install_result["result"]
    
    # Test checking plugin status
    status_result = await plugin_manager.handle_task(
        "Check git plugin status"
    )
    assert status_result["status"] == "success"
    assert "plugin_status" in status_result["result"]
    
    # Test updating plugin
    update_result = await plugin_manager.handle_task(
        "Update git plugin to latest version"
    )
    assert update_result["status"] == "success"
    assert "update_status" in update_result["result"]

async def test_agent_coordination(supervisor):
    """Test coordination between agents."""
    # Create a task that requires multiple agents
    result = await supervisor.handle_task(
        "Create a new pipeline job that builds a Java project and analyze its logs"
    )
    assert result["status"] == "success"
    assert "pipeline" in result["result"]
    assert "analysis" in result["result"]
    
    # Verify that both pipeline and log analysis were performed
    assert "stages" in result["result"]["pipeline"]
    assert "recommendations" in result["result"]["analysis"]

async def test_error_handling(supervisor):
    """Test error handling in agents."""
    # Test with invalid agent type
    invalid_result = await supervisor.handle_task(
        "Test task",
        agent_type="invalid_agent"
    )
    assert invalid_result["status"] == "error"
    assert "error" in invalid_result
    
    # Test with invalid task format
    error_result = await supervisor.handle_task("")
    assert error_result["status"] == "error"
    assert "error" in error_result

async def test_concurrent_tasks(supervisor):
    """Test handling of concurrent tasks."""
    import asyncio
    
    # Create multiple tasks
    tasks = [
        supervisor.handle_task(f"Task {i}")
        for i in range(5)
    ]
    
    # Run tasks concurrently
    results = await asyncio.gather(*tasks)
    
    # Verify all tasks completed
    assert len(results) == 5
    assert all(r["status"] in ["success", "error"] for r in results)