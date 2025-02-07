"""Unit tests for MongoDB client."""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from langchain_jenkins.db.mongo_client import MongoClient

@pytest.fixture
def mongo_client():
    """Create a MongoDB client for testing."""
    client = MongoClient()
    client.logs = AsyncMock()
    client.errors = AsyncMock()
    client.trends = AsyncMock()
    return client

@pytest.fixture
def sample_log():
    """Create a sample build log."""
    return {
        "build_id": "123",
        "job_name": "test-job",
        "log_text": "Build log content",
        "timestamp": datetime.utcnow(),
        "metadata": {"branch": "main"}
    }

@pytest.fixture
def sample_error():
    """Create a sample build error."""
    return {
        "build_id": "123",
        "job_name": "test-job",
        "error_type": "OutOfMemoryError",
        "error_message": "Java heap space",
        "stack_trace": "at java.base/...",
        "timestamp": datetime.utcnow(),
        "metadata": {"severity": "high"}
    }

@pytest.mark.asyncio
async def test_store_build_log(mongo_client, sample_log):
    """Test storing build log."""
    mongo_client.logs.insert_one = AsyncMock(
        return_value=AsyncMock(inserted_id="abc123")
    )
    
    result = await mongo_client.store_build_log(
        sample_log["build_id"],
        sample_log["job_name"],
        sample_log["log_text"],
        sample_log["metadata"]
    )
    
    assert result["status"] == "stored"
    assert result["build_id"] == "123"
    assert result["id"] == "abc123"

@pytest.mark.asyncio
async def test_store_build_error(mongo_client, sample_error):
    """Test storing build error."""
    mongo_client.errors.insert_one = AsyncMock(
        return_value=AsyncMock(inserted_id="abc123")
    )
    mongo_client._update_error_trends = AsyncMock()
    
    result = await mongo_client.store_build_error(
        sample_error["build_id"],
        sample_error["job_name"],
        sample_error["error_type"],
        sample_error["error_message"],
        sample_error["stack_trace"],
        sample_error["metadata"]
    )
    
    assert result["status"] == "stored"
    assert result["build_id"] == "123"
    assert result["id"] == "abc123"

@pytest.mark.asyncio
async def test_update_error_trends(mongo_client):
    """Test updating error trends."""
    mongo_client.trends.update_one = AsyncMock()
    
    await mongo_client._update_error_trends(
        "test-job",
        "OutOfMemoryError",
        "Java heap space"
    )
    
    mongo_client.trends.update_one.assert_called_once()
    args = mongo_client.trends.update_one.call_args[0]
    assert args[0]["job_name"] == "test-job"
    assert args[0]["error_type"] == "OutOfMemoryError"

@pytest.mark.asyncio
async def test_get_build_log(mongo_client, sample_log):
    """Test getting build log."""
    mongo_client.logs.find_one = AsyncMock(return_value=sample_log)
    
    result = await mongo_client.get_build_log("123")
    
    assert result == sample_log
    mongo_client.logs.find_one.assert_called_with({"build_id": "123"})

@pytest.mark.asyncio
async def test_get_build_errors(mongo_client, sample_error):
    """Test getting build errors."""
    mongo_client.errors.find = AsyncMock()
    mongo_client.errors.find.return_value.to_list = AsyncMock(
        return_value=[sample_error]
    )
    
    result = await mongo_client.get_build_errors("123")
    
    assert len(result) == 1
    assert result[0] == sample_error
    mongo_client.errors.find.assert_called_with({"build_id": "123"})

@pytest.mark.asyncio
async def test_get_job_logs(mongo_client, sample_log):
    """Test getting job logs."""
    mongo_client.logs.find = AsyncMock()
    mongo_client.logs.find.return_value.sort = AsyncMock()
    mongo_client.logs.find.return_value.sort.return_value.limit = AsyncMock()
    mongo_client.logs.find.return_value.sort.return_value.limit.return_value.to_list = AsyncMock(
        return_value=[sample_log]
    )
    
    result = await mongo_client.get_job_logs("test-job", 10)
    
    assert len(result) == 1
    assert result[0] == sample_log
    mongo_client.logs.find.assert_called_with({"job_name": "test-job"})

@pytest.mark.asyncio
async def test_get_job_errors(mongo_client, sample_error):
    """Test getting job errors."""
    mongo_client.errors.find = AsyncMock()
    mongo_client.errors.find.return_value.sort = AsyncMock()
    mongo_client.errors.find.return_value.sort.return_value.limit = AsyncMock()
    mongo_client.errors.find.return_value.sort.return_value.limit.return_value.to_list = AsyncMock(
        return_value=[sample_error]
    )
    
    result = await mongo_client.get_job_errors("test-job", 10)
    
    assert len(result) == 1
    assert result[0] == sample_error
    mongo_client.errors.find.assert_called_with({"job_name": "test-job"})

@pytest.mark.asyncio
async def test_get_error_trends(mongo_client):
    """Test getting error trends."""
    trends = [
        {
            "job_name": "test-job",
            "error_type": "OutOfMemoryError",
            "date": datetime.utcnow(),
            "count": 5,
            "messages": ["Java heap space"]
        }
    ]
    
    mongo_client.trends.find = AsyncMock()
    mongo_client.trends.find.return_value.sort = AsyncMock()
    mongo_client.trends.find.return_value.sort.return_value.to_list = AsyncMock(
        return_value=trends
    )
    
    result = await mongo_client.get_error_trends("test-job", 7)
    
    assert len(result) == 1
    assert result[0]["job_name"] == "test-job"
    assert result[0]["count"] == 5

@pytest.mark.asyncio
async def test_get_common_errors(mongo_client):
    """Test getting common errors."""
    errors = [
        {
            "_id": {
                "job_name": "test-job",
                "error_type": "OutOfMemoryError"
            },
            "total_count": 10,
            "messages": [["Java heap space"]]
        }
    ]
    
    mongo_client.trends.aggregate = AsyncMock()
    mongo_client.trends.aggregate.return_value.to_list = AsyncMock(
        return_value=errors
    )
    
    result = await mongo_client.get_common_errors("test-job", 7, 10)
    
    assert len(result) == 1
    assert result[0]["_id"]["job_name"] == "test-job"
    assert result[0]["total_count"] == 10

@pytest.mark.asyncio
async def test_get_error_patterns(mongo_client):
    """Test getting error patterns."""
    trends = [
        {
            "job_name": "test-job",
            "error_type": "OutOfMemoryError",
            "date": datetime.utcnow(),
            "count": 5,
            "messages": ["Java heap space"]
        }
    ]
    
    mongo_client.get_error_trends = AsyncMock(return_value=trends)
    
    result = await mongo_client.get_error_patterns("test-job", 7)
    
    assert len(result) == 1
    assert result[0]["job_name"] == "test-job"
    assert result[0]["frequency"] == 5

@pytest.mark.asyncio
async def test_get_error_correlations(mongo_client):
    """Test getting error correlations."""
    errors = [
        {
            "job_name": "test-job",
            "error_type": "OutOfMemoryError",
            "timestamp": datetime.utcnow()
        },
        {
            "job_name": "test-job",
            "error_type": "NullPointerException",
            "timestamp": datetime.utcnow()
        }
    ]
    
    mongo_client.errors.find = AsyncMock()
    mongo_client.errors.find.return_value.to_list = AsyncMock(
        return_value=errors
    )
    
    result = await mongo_client.get_error_correlations("test-job", 7)
    
    assert len(result) == 2
    assert result[0]["job_name"] == "test-job"
    assert len(result[0]["related_errors"]) > 0