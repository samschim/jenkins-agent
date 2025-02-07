"""Integration tests for Jenkins API."""
import pytest
import os
from langchain_jenkins.tools.jenkins_api import JenkinsAPI
from langchain_jenkins.utils.errors import (
    JenkinsAuthError,
    JenkinsNotFoundError
)

@pytest.fixture
def jenkins_api():
    """Create a Jenkins API client for testing."""
    return JenkinsAPI()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_job_info(jenkins_api):
    """Test getting job information."""
    # Create a test job first
    job_name = "test-job"
    try:
        result = await jenkins_api.get_job_info(job_name)
        assert result is not None
        assert "name" in result
        assert result["name"] == job_name
    except JenkinsNotFoundError:
        pytest.skip("Test job not found")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_build_job(jenkins_api):
    """Test triggering a build."""
    job_name = "test-job"
    try:
        result = await jenkins_api.build_job(job_name)
        assert result is not None
        assert "status" in result
    except JenkinsNotFoundError:
        pytest.skip("Test job not found")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_build_log(jenkins_api):
    """Test getting build logs."""
    job_name = "test-job"
    try:
        result = await jenkins_api.get_build_log(job_name)
        assert isinstance(result, str)
    except JenkinsNotFoundError:
        pytest.skip("Test job not found")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_plugins(jenkins_api):
    """Test getting plugin information."""
    result = await jenkins_api.get_plugins()
    assert result is not None
    assert "plugins" in result
    assert isinstance(result["plugins"], list)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_system_info(jenkins_api):
    """Test getting system information."""
    result = await jenkins_api.get_system_info()
    assert result is not None
    assert "jobs" in result
    assert isinstance(result["jobs"], list)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_invalid_credentials():
    """Test handling of invalid credentials."""
    # Create API client with invalid credentials
    api = JenkinsAPI()
    api.auth = ("invalid", "invalid")
    
    with pytest.raises(JenkinsAuthError):
        await api.get_system_info()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_nonexistent_job(jenkins_api):
    """Test handling of non-existent job."""
    with pytest.raises(JenkinsNotFoundError):
        await jenkins_api.get_job_info("nonexistent-job-12345")