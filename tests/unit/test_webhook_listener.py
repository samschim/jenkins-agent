"""Unit tests for webhook listener."""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from langchain_jenkins.webhooks.listener import app

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)

@pytest.fixture
def sample_build_payload():
    """Create sample build payload."""
    return {
        "build": {
            "full_url": "http://jenkins/job/test-job/123/",
            "number": 123,
            "status": "FAILURE",
            "phase": "COMPLETED",
            "duration": 300,
            "parameters": {"branch": "main"},
            "artifacts": [
                {
                    "fileName": "test.jar",
                    "relativePath": "target/test.jar",
                    "url": "http://jenkins/job/test-job/123/artifact/target/test.jar"
                }
            ]
        }
    }

@pytest.fixture
def sample_scm_payload():
    """Create sample SCM payload."""
    return {
        "scm": {
            "url": "https://github.com/test/repo",
            "branch": "main",
            "commit": "abc123",
            "changes": [
                {
                    "file": "src/main.py",
                    "author": {"name": "Test User"},
                    "message": "Update code"
                }
            ]
        }
    }

def test_parse_build_event(sample_build_payload):
    """Test parsing build event."""
    from langchain_jenkins.webhooks.listener import _parse_build_event
    
    event = _parse_build_event(sample_build_payload["build"])
    
    assert event["job_name"] == "test-job"
    assert event["build_number"] == 123
    assert event["status"] == "FAILURE"
    assert event["phase"] == "COMPLETED"
    assert event["duration"] == 300
    assert len(event["artifacts"]) == 1
    assert event["artifacts"][0]["name"] == "test.jar"

def test_parse_scm_event(sample_scm_payload):
    """Test parsing SCM event."""
    from langchain_jenkins.webhooks.listener import _parse_scm_event
    
    event = _parse_scm_event(sample_scm_payload["scm"])
    
    assert event["url"] == "https://github.com/test/repo"
    assert event["branch"] == "main"
    assert event["commit"] == "abc123"
    assert len(event["changes"]) == 1
    assert event["changes"][0]["file"] == "src/main.py"

def test_should_alert():
    """Test alert conditions."""
    from langchain_jenkins.webhooks.listener import _should_alert
    
    # Test build failure
    event = {
        "type": "build",
        "status": "FAILURE",
        "job_name": "test-job",
        "duration": 300
    }
    assert _should_alert(event) is True
    
    # Test successful build
    event["status"] = "SUCCESS"
    assert _should_alert(event) is False
    
    # Test critical job
    with patch("langchain_jenkins.webhooks.listener.config") as mock_config:
        mock_config.alerts.critical_jobs = ["test-job"]
        mock_config.alerts.max_build_duration = 600
        event["status"] = "UNSTABLE"
        assert _should_alert(event) is True

def test_get_alert_severity():
    """Test alert severity levels."""
    from langchain_jenkins.webhooks.listener import _get_alert_severity
    
    # Test critical job
    with patch("langchain_jenkins.webhooks.listener.config") as mock_config:
        mock_config.alerts.critical_jobs = ["test-job"]
        event = {
            "type": "build",
            "job_name": "test-job",
            "status": "FAILURE"
        }
        assert _get_alert_severity(event) == "critical"
    
    # Test failure
    event["job_name"] = "other-job"
    assert _get_alert_severity(event) == "high"
    
    # Test unstable
    event["status"] = "UNSTABLE"
    assert _get_alert_severity(event) == "medium"
    
    # Test success
    event["status"] = "SUCCESS"
    assert _get_alert_severity(event) == "low"

@pytest.mark.asyncio
async def test_webhook_endpoint(client, sample_build_payload):
    """Test webhook endpoint."""
    with patch("langchain_jenkins.webhooks.listener.redis") as mock_redis, \
         patch("langchain_jenkins.webhooks.listener._store_build_event") as mock_store, \
         patch("langchain_jenkins.webhooks.listener._publish_alert") as mock_alert:
        
        mock_redis.lpush = AsyncMock()
        
        response = client.post(
            "/webhook",
            json=sample_build_payload
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert mock_redis.lpush.called
        assert mock_store.called
        assert mock_alert.called

@pytest.mark.asyncio
async def test_store_build_event(sample_build_payload):
    """Test storing build event."""
    from langchain_jenkins.webhooks.listener import _store_build_event
    
    with patch("langchain_jenkins.webhooks.listener.mongo_client") as mock_mongo:
        mock_mongo.store_build_log = AsyncMock()
        mock_mongo.store_build_error = AsyncMock()
        
        event = {
            "type": "build",
            "job_name": "test-job",
            "build_number": 123,
            "status": "FAILURE",
            "phase": "COMPLETED",
            "duration": 300,
            "url": "http://jenkins/job/test-job/123/"
        }
        
        await _store_build_event(event)
        
        assert mock_mongo.store_build_log.called
        assert mock_mongo.store_build_error.called