"""Unit tests for error handling module."""
import pytest
import httpx
from unittest.mock import AsyncMock, patch
from langchain_jenkins.utils.errors import (
    JenkinsError,
    JenkinsAPIError,
    JenkinsAuthError,
    JenkinsNotFoundError,
    handle_jenkins_error,
    error_handler,
    validate_response,
    retry_on_error
)

def test_jenkins_error():
    """Test JenkinsError class."""
    error = JenkinsError(
        "Test error",
        status_code=500,
        details={"key": "value"}
    )
    assert str(error) == "Test error"
    assert error.status_code == 500
    assert error.details == {"key": "value"}

def test_handle_jenkins_error():
    """Test error handling function."""
    error = JenkinsAPIError(
        "API error",
        status_code=500,
        details={"response": "error"}
    )
    context = {"function": "test_func"}
    
    result = handle_jenkins_error(error, context)
    
    assert result["status"] == "error"
    assert result["error_type"] == "JenkinsAPIError"
    assert result["message"] == "API error"
    assert result["context"] == context
    assert result["status_code"] == 500
    assert result["details"] == {"response": "error"}

@pytest.mark.asyncio
async def test_error_handler_decorator():
    """Test error handler decorator."""
    @error_handler
    async def test_func():
        raise JenkinsAPIError("Test error")
    
    result = await test_func()
    
    assert result["status"] == "error"
    assert result["error_type"] == "JenkinsAPIError"
    assert result["message"] == "Test error"

def test_validate_response_auth_error():
    """Test response validation with auth error."""
    response = AsyncMock(spec=httpx.Response)
    response.status_code = 401
    response.text = "Unauthorized"
    
    with pytest.raises(JenkinsAuthError) as exc:
        validate_response(response)
    assert exc.value.status_code == 401

def test_validate_response_not_found():
    """Test response validation with not found error."""
    response = AsyncMock(spec=httpx.Response)
    response.status_code = 404
    response.text = "Not Found"
    
    with pytest.raises(JenkinsNotFoundError) as exc:
        validate_response(response)
    assert exc.value.status_code == 404

@pytest.mark.asyncio
async def test_retry_on_error_decorator():
    """Test retry decorator."""
    mock_func = AsyncMock(side_effect=[
        JenkinsAPIError("Attempt 1"),
        JenkinsAPIError("Attempt 2"),
        "success"
    ])
    
    @retry_on_error(max_retries=3, delay=0)
    async def test_func():
        return await mock_func()
    
    result = await test_func()
    assert result == "success"
    assert mock_func.call_count == 3

@pytest.mark.asyncio
async def test_retry_on_error_max_retries():
    """Test retry decorator with max retries exceeded."""
    mock_func = AsyncMock(side_effect=JenkinsAPIError("Error"))
    
    @retry_on_error(max_retries=3, delay=0)
    async def test_func():
        return await mock_func()
    
    result = await test_func()
    assert result["status"] == "error"
    assert result["error_type"] == "JenkinsAPIError"
    assert mock_func.call_count == 3