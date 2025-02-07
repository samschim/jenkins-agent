"""Test enhanced pipeline manager functionality."""
import pytest
from langchain_jenkins.agents.enhanced_pipeline_manager import EnhancedPipelineManager

pytestmark = pytest.mark.asyncio

async def test_create_pipeline(mock_jenkins_api, mock_llm):
    """Test creating a new pipeline."""
    manager = EnhancedPipelineManager()
    
    # Test Java pipeline creation
    result = await manager.handle_task(
        "Create a new pipeline for Java project with testing and deployment"
    )
    
    assert result["status"] == "success"
    assert "pipeline" in result
    assert "test" in result["pipeline"].lower()
    assert "deploy" in result["pipeline"].lower()
    
    # Test Python pipeline creation
    result = await manager.handle_task(
        "Create a new Python pipeline with code coverage"
    )
    
    assert result["status"] == "success"
    assert "pipeline" in result
    assert "python" in result["pipeline"].lower()
    assert "coverage" in result["pipeline"].lower()

async def test_scan_pipeline(mock_jenkins_api, mock_llm):
    """Test scanning a pipeline."""
    manager = EnhancedPipelineManager()
    
    result = await manager.handle_task(
        "Scan my-pipeline for security issues"
    )
    
    assert result["status"] == "success"
    assert "findings" in result
    assert "analysis" in result

async def test_secure_pipeline(mock_jenkins_api, mock_llm):
    """Test securing a pipeline."""
    manager = EnhancedPipelineManager()
    
    result = await manager.handle_task(
        "Secure my-pipeline"
    )
    
    assert result["status"] == "success"
    assert "secured_pipeline" in result
    assert "improvements" in result
    assert "verification" in result

async def test_optimize_pipeline(mock_jenkins_api, mock_llm):
    """Test optimizing a pipeline."""
    manager = EnhancedPipelineManager()
    
    result = await manager.handle_task(
        "Optimize my-java-pipeline for better performance"
    )
    
    assert result["status"] == "success"
    assert "optimized_pipeline" in result
    assert "improvements" in result
    assert "benefits" in result

async def test_validate_pipeline(mock_jenkins_api, mock_llm):
    """Test validating a pipeline."""
    manager = EnhancedPipelineManager()
    
    result = await manager.handle_task(
        "Validate my-pipeline configuration"
    )
    
    assert result["status"] == "success"
    assert "security" in result
    assert "validation" in result
    assert isinstance(result["valid"], bool)

async def test_project_type_extraction():
    """Test project type extraction."""
    manager = EnhancedPipelineManager()
    
    assert manager._extract_project_type("Create Java pipeline") == "java"
    assert manager._extract_project_type("New Python project") == "python"
    assert manager._extract_project_type("Setup Node.js pipeline") == "node"
    assert manager._extract_project_type("Docker build pipeline") == "docker"
    assert manager._extract_project_type("Generic pipeline") == "java"  # default

async def test_requirements_extraction():
    """Test requirements extraction."""
    manager = EnhancedPipelineManager()
    
    requirements = manager._extract_requirements(
        "Create pipeline with testing, deployment, and code coverage"
    )
    
    assert "Include testing stage" in requirements
    assert "Include deployment stage" in requirements
    assert "Include code coverage" in requirements

async def test_error_handling(mock_jenkins_api, mock_llm):
    """Test error handling."""
    manager = EnhancedPipelineManager()
    
    # Test invalid task
    result = await manager.handle_task(
        "Invalid task"
    )
    assert result["status"] == "error"
    assert "error" in result
    
    # Test missing pipeline
    result = await manager.handle_task(
        "Scan nonexistent-pipeline"
    )
    assert result["status"] == "error"
    assert "error" in result

async def test_complex_tasks(mock_jenkins_api, mock_llm):
    """Test handling of complex tasks."""
    manager = EnhancedPipelineManager()
    
    # Create and validate pipeline
    result = await manager.handle_task(
        "Create a secure Python pipeline with testing and deployment"
    )
    
    assert result["status"] == "success"
    assert "pipeline" in result
    assert "python" in result["pipeline"].lower()
    assert "test" in result["pipeline"].lower()
    assert "deploy" in result["pipeline"].lower()
    
    # Optimize and secure pipeline
    result = await manager.handle_task(
        "Optimize and secure my-pipeline"
    )
    
    assert result["status"] == "success"
    assert "optimized_pipeline" in result
    assert "security" in result