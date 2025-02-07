"""Unit tests for enhanced build manager agent."""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from langchain_jenkins.agents.enhanced_build_manager import (
    EnhancedBuildManagerAgent,
    BuildInfo
)

@pytest.fixture
def build_manager():
    """Create a build manager for testing."""
    manager = EnhancedBuildManagerAgent()
    manager.jenkins = AsyncMock()
    manager.log_analyzer = AsyncMock()
    return manager

@pytest.mark.asyncio
async def test_start_build(build_manager):
    """Test build start with priority."""
    build_manager.jenkins.post.return_value = {"queueNumber": 123}
    build_manager.jenkins.build_job.return_value = {"queueNumber": 123}
    
    result = await build_manager._start_build(
        "test-job",
        priority="high"
    )
    
    assert result["status"] == "started"
    assert result["job"] == "test-job"
    assert result["priority"] == "high"
    assert result["queue_number"] == 123

@pytest.mark.asyncio
async def test_stop_build(build_manager):
    """Test build stop."""
    build_manager.jenkins.post.return_value = {}
    build_manager._get_build_status = AsyncMock(
        return_value={"number": 42}
    )
    
    result = await build_manager._stop_build("test-job")
    
    assert result["status"] == "stopped"
    assert result["job"] == "test-job"
    assert result["build"] == 42

@pytest.mark.asyncio
async def test_restart_build(build_manager):
    """Test build restart."""
    build_manager._stop_build = AsyncMock()
    build_manager._start_build = AsyncMock(
        return_value={
            "status": "started",
            "job": "test-job",
            "queue_number": 123
        }
    )
    
    result = await build_manager._restart_build("test-job")
    
    assert result["status"] == "started"
    assert result["job"] == "test-job"
    assert result["queue_number"] == 123

@pytest.mark.asyncio
async def test_get_build_history(build_manager):
    """Test build history retrieval."""
    build_manager.jenkins.get.return_value = {
        "builds": [
            {
                "number": 42,
                "status": "SUCCESS",
                "timestamp": 1644825600000,  # 2022-02-14 12:00:00
                "duration": 300000,
                "result": "SUCCESS",
                "url": "http://jenkins/job/test/42",
                "changeSet": {"items": []},
                "artifacts": []
            }
        ]
    }
    
    result = await build_manager._get_build_history("test-job", limit=1)
    
    assert len(result) == 1
    assert isinstance(result[0], BuildInfo)
    assert result[0].number == 42
    assert result[0].status == "SUCCESS"
    assert result[0].duration == 300000

@pytest.mark.asyncio
async def test_manage_dependencies(build_manager):
    """Test dependency management."""
    build_manager.jenkins.get.return_value = """
        <project>
            <upstreamProjects/>
            <downstreamProjects/>
        </project>
    """
    build_manager.jenkins.post.return_value = {}
    
    result = await build_manager._manage_dependencies(
        "test-job",
        upstream_jobs=["job1", "job2"],
        downstream_jobs=["job3", "job4"]
    )
    
    assert result["status"] == "updated"
    assert result["job"] == "test-job"
    assert result["upstream_jobs"] == ["job1", "job2"]
    assert result["downstream_jobs"] == ["job3", "job4"]

@pytest.mark.asyncio
async def test_handle_task_build_trigger(build_manager):
    """Test build trigger task handling."""
    build_manager._start_build = AsyncMock(
        return_value={
            "status": "started",
            "job": "test-job",
            "queue_number": 123
        }
    )
    
    result = await build_manager.handle_task(
        "start build for test-job with high priority"
    )
    
    assert result["status"] == "started"
    assert result["job"] == "test-job"
    assert result["queue_number"] == 123

@pytest.mark.asyncio
async def test_handle_task_build_stop(build_manager):
    """Test build stop task handling."""
    build_manager._stop_build = AsyncMock(
        return_value={
            "status": "stopped",
            "job": "test-job",
            "build": 42
        }
    )
    
    result = await build_manager.handle_task(
        "stop build for test-job"
    )
    
    assert result["status"] == "stopped"
    assert result["job"] == "test-job"
    assert result["build"] == 42

@pytest.mark.asyncio
async def test_handle_task_build_history(build_manager):
    """Test build history task handling."""
    build_manager._get_build_history = AsyncMock(
        return_value=[
            BuildInfo(
                number=42,
                status="SUCCESS",
                timestamp=datetime.now(),
                duration=300000,
                result="SUCCESS",
                url="http://jenkins/job/test/42",
                changes=[],
                artifacts=[]
            )
        ]
    )
    
    result = await build_manager.handle_task(
        "get build history for test-job limit 1"
    )
    
    assert result["status"] == "success"
    assert result["job"] == "test-job"
    assert len(result["history"]) == 1
    assert result["history"][0]["number"] == 42

@pytest.mark.asyncio
async def test_handle_task_dependency_management(build_manager):
    """Test dependency management task handling."""
    build_manager._manage_dependencies = AsyncMock(
        return_value={
            "status": "updated",
            "job": "test-job",
            "upstream_jobs": ["job1", "job2"],
            "downstream_jobs": ["job3", "job4"]
        }
    )
    
    result = await build_manager.handle_task(
        "set dependencies for test-job upstream job1 job2 downstream job3 job4"
    )
    
    assert result["status"] == "updated"
    assert result["job"] == "test-job"
    assert result["upstream_jobs"] == ["job1", "job2"]
    assert result["downstream_jobs"] == ["job3", "job4"]

@pytest.mark.asyncio
async def test_handle_task_build_log(build_manager):
    """Test build log task handling."""
    build_manager.jenkins.get_build_log.return_value = "Build log content"
    build_manager.log_analyzer.analyze_build_log.return_value = {
        "errors": [],
        "warnings": []
    }
    
    result = await build_manager.handle_task(
        "analyze build log for test-job"
    )
    
    assert result["status"] == "success"
    assert result["job"] == "test-job"
    assert result["log"] == "Build log content"
    assert "analysis" in result