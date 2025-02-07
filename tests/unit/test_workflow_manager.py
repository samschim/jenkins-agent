"""Unit tests for workflow manager."""
import pytest
from unittest.mock import AsyncMock, patch
from langchain_jenkins.agents.workflow_manager import (
    WorkflowManager,
    WorkflowState,
    AgentState
)

@pytest.fixture
def workflow_manager():
    """Create a workflow manager for testing."""
    manager = WorkflowManager()
    manager.llm = AsyncMock()
    return manager

@pytest.fixture
def sample_state():
    """Create a sample workflow state."""
    return WorkflowState(
        task="Start build for test-job",
        current_agent="supervisor",
        agents={},
        messages=[],
        artifacts={}
    )

@pytest.mark.asyncio
async def test_supervisor_node(workflow_manager, sample_state):
    """Test supervisor node logic."""
    workflow_manager.llm.agenerate.return_value.generations[0].text = """{
        "agent": "build_manager",
        "reason": "Task involves build operation",
        "subtasks": [
            {
                "agent": "log_analyzer",
                "task": "Analyze build logs"
            }
        ]
    }"""
    
    result = await workflow_manager._supervisor_node(sample_state)
    
    assert result.current_agent == "build_manager"
    assert "build_manager" in result.agents
    assert "log_analyzer" in result.agents
    assert len(result.messages) == 1

@pytest.mark.asyncio
async def test_build_manager_node(workflow_manager, sample_state):
    """Test build manager node logic."""
    sample_state.current_agent = "build_manager"
    sample_state.agents["build_manager"] = AgentState(
        task="Start build for test-job",
        agent_type="build_manager",
        status="pending"
    )
    
    with patch("langchain_jenkins.agents.workflow_manager.build_manager") as mock_manager:
        mock_manager.handle_task = AsyncMock(return_value={
            "status": "success",
            "job": "test-job",
            "artifacts": {"build_id": "123"}
        })
        
        result = await workflow_manager._build_manager_node(sample_state)
        
        assert result.agents["build_manager"].status == "success"
        assert "build" in result.artifacts
        assert len(result.messages) == 1

@pytest.mark.asyncio
async def test_log_analyzer_node(workflow_manager, sample_state):
    """Test log analyzer node logic."""
    sample_state.current_agent = "log_analyzer"
    sample_state.agents["log_analyzer"] = AgentState(
        task="Analyze build logs",
        agent_type="log_analyzer",
        status="pending"
    )
    
    with patch("langchain_jenkins.agents.workflow_manager.log_analyzer") as mock_analyzer:
        mock_analyzer.handle_task = AsyncMock(return_value={
            "status": "success",
            "analysis": {"errors": []}
        })
        
        result = await workflow_manager._log_analyzer_node(sample_state)
        
        assert result.agents["log_analyzer"].status == "success"
        assert "logs" in result.artifacts
        assert len(result.messages) == 1

@pytest.mark.asyncio
async def test_pipeline_manager_node(workflow_manager, sample_state):
    """Test pipeline manager node logic."""
    sample_state.current_agent = "pipeline_manager"
    sample_state.agents["pipeline_manager"] = AgentState(
        task="Update pipeline config",
        agent_type="pipeline_manager",
        status="pending"
    )
    
    with patch("langchain_jenkins.agents.workflow_manager.pipeline_manager") as mock_manager:
        mock_manager.handle_task = AsyncMock(return_value={
            "status": "success",
            "pipeline": {"name": "test-pipeline"}
        })
        
        result = await workflow_manager._pipeline_manager_node(sample_state)
        
        assert result.agents["pipeline_manager"].status == "success"
        assert "pipeline" in result.artifacts
        assert len(result.messages) == 1

@pytest.mark.asyncio
async def test_plugin_manager_node(workflow_manager, sample_state):
    """Test plugin manager node logic."""
    sample_state.current_agent = "plugin_manager"
    sample_state.agents["plugin_manager"] = AgentState(
        task="Install plugin",
        agent_type="plugin_manager",
        status="pending"
    )
    
    with patch("langchain_jenkins.agents.workflow_manager.plugin_manager") as mock_manager:
        mock_manager.handle_task = AsyncMock(return_value={
            "status": "success",
            "plugins": [{"name": "git"}]
        })
        
        result = await workflow_manager._plugin_manager_node(sample_state)
        
        assert result.agents["plugin_manager"].status == "success"
        assert "plugins" in result.artifacts
        assert len(result.messages) == 1

@pytest.mark.asyncio
async def test_needs_coordination(workflow_manager, sample_state):
    """Test coordination check."""
    workflow_manager.llm.agenerate.return_value.generations[0].text = """{
        "next_agent": "log_analyzer",
        "reason": "Need to analyze build logs",
        "coordination": [
            {
                "type": "share_artifact",
                "source": "build",
                "target": "log_analyzer"
            }
        ]
    }"""
    
    sample_state.artifacts["build"] = {"build_id": "123"}
    
    needs_coord = await workflow_manager._needs_coordination(sample_state)
    
    assert needs_coord is True
    assert sample_state.current_agent == "log_analyzer"
    assert "log_analyzer" in sample_state.agents
    assert len(sample_state.messages) == 1

def test_routing_conditions(workflow_manager, sample_state):
    """Test routing conditions."""
    # Test build manager routing
    sample_state.current_agent = "build_manager"
    assert workflow_manager._should_route_to_build(sample_state) is True
    assert workflow_manager._should_route_to_logs(sample_state) is False
    
    # Test log analyzer routing
    sample_state.current_agent = "log_analyzer"
    assert workflow_manager._should_route_to_logs(sample_state) is True
    assert workflow_manager._should_route_to_build(sample_state) is False
    
    # Test pipeline manager routing
    sample_state.current_agent = "pipeline_manager"
    assert workflow_manager._should_route_to_pipeline(sample_state) is True
    assert workflow_manager._should_route_to_plugin(sample_state) is False
    
    # Test plugin manager routing
    sample_state.current_agent = "plugin_manager"
    assert workflow_manager._should_route_to_plugin(sample_state) is True
    assert workflow_manager._should_route_to_pipeline(sample_state) is False

def test_workflow_completion(workflow_manager, sample_state):
    """Test workflow completion check."""
    # No agents - not complete
    assert workflow_manager._is_workflow_complete(sample_state) is True
    
    # Pending agent - not complete
    sample_state.agents["build_manager"] = AgentState(
        task="Start build",
        agent_type="build_manager",
        status="pending"
    )
    assert workflow_manager._is_workflow_complete(sample_state) is False
    
    # All agents complete - complete
    sample_state.agents["build_manager"].status = "success"
    sample_state.agents["log_analyzer"] = AgentState(
        task="Analyze logs",
        agent_type="log_analyzer",
        status="success"
    )
    assert workflow_manager._is_workflow_complete(sample_state) is True
    
    # Error is also considered complete
    sample_state.agents["plugin_manager"] = AgentState(
        task="Install plugin",
        agent_type="plugin_manager",
        status="error"
    )
    assert workflow_manager._is_workflow_complete(sample_state) is True

@pytest.mark.asyncio
async def test_execute_workflow(workflow_manager, sample_state):
    """Test workflow execution."""
    # Mock supervisor routing
    workflow_manager.llm.agenerate.side_effect = [
        AsyncMock(generations=[AsyncMock(text="""{
            "agent": "build_manager",
            "reason": "Task involves build operation",
            "subtasks": []
        }""")]),
        AsyncMock(generations=[AsyncMock(text="""{
            "next_agent": "end",
            "reason": "Task completed",
            "coordination": []
        }""")])
    ]
    
    # Mock build manager
    with patch("langchain_jenkins.agents.workflow_manager.build_manager") as mock_manager:
        mock_manager.handle_task = AsyncMock(return_value={
            "status": "success",
            "job": "test-job"
        })
        
        result = await workflow_manager.execute_workflow(
            "Start build for test-job"
        )
        
        assert result["status"] == "success"
        assert "build_manager" in result["agents"]
        assert len(result["messages"]) > 0
        assert isinstance(result["artifacts"], dict)