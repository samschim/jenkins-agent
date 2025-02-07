"""Unit tests for notification service."""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from langchain_jenkins.webhooks.notifier import NotificationService

@pytest.fixture
def notifier():
    """Create notification service for testing."""
    service = NotificationService()
    service.redis = AsyncMock()
    service.http = AsyncMock()
    return service

@pytest.fixture
def sample_alert():
    """Create sample alert data."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "type": "jenkins_alert",
        "severity": "high",
        "message": "Build failed",
        "event": {
            "type": "build",
            "job_name": "test-job",
            "build_number": 123,
            "status": "FAILURE",
            "phase": "COMPLETED",
            "duration": 300,
            "url": "http://jenkins/job/test-job/123/"
        }
    }

@pytest.mark.asyncio
async def test_process_alert_critical(notifier, sample_alert):
    """Test processing critical alert."""
    sample_alert["severity"] = "critical"
    
    with patch.object(notifier, "_send_slack_alert") as mock_slack, \
         patch.object(notifier, "_send_telegram_alert") as mock_telegram, \
         patch.object(notifier, "_send_email_alert") as mock_email:
        
        await notifier._process_alert(sample_alert)
        
        assert mock_slack.called
        assert mock_telegram.called
        assert mock_email.called

@pytest.mark.asyncio
async def test_process_alert_high(notifier, sample_alert):
    """Test processing high severity alert."""
    sample_alert["severity"] = "high"
    
    with patch.object(notifier, "_send_slack_alert") as mock_slack, \
         patch.object(notifier, "_send_telegram_alert") as mock_telegram, \
         patch.object(notifier, "_send_email_alert") as mock_email:
        
        await notifier._process_alert(sample_alert)
        
        assert mock_slack.called
        assert mock_telegram.called
        assert not mock_email.called

@pytest.mark.asyncio
async def test_process_alert_low(notifier, sample_alert):
    """Test processing low severity alert."""
    sample_alert["severity"] = "low"
    
    with patch.object(notifier, "_send_slack_alert") as mock_slack, \
         patch.object(notifier, "_send_telegram_alert") as mock_telegram, \
         patch.object(notifier, "_send_email_alert") as mock_email:
        
        await notifier._process_alert(sample_alert)
        
        assert mock_slack.called
        assert not mock_telegram.called
        assert not mock_email.called

@pytest.mark.asyncio
async def test_send_slack_alert(notifier, sample_alert):
    """Test sending Slack alert."""
    with patch("langchain_jenkins.webhooks.notifier.config") as mock_config:
        mock_config.slack.webhook_url = "https://slack.com/webhook"
        
        await notifier._send_slack_alert(sample_alert)
        
        notifier.http.post.assert_called_once_with(
            "https://slack.com/webhook",
            json=notifier._format_slack_message(sample_alert)
        )

@pytest.mark.asyncio
async def test_send_telegram_alert(notifier, sample_alert):
    """Test sending Telegram alert."""
    with patch("langchain_jenkins.webhooks.notifier.config") as mock_config:
        mock_config.telegram.bot_token = "bot123"
        mock_config.telegram.chat_id = "chat123"
        
        await notifier._send_telegram_alert(sample_alert)
        
        notifier.http.post.assert_called_once_with(
            "https://api.telegram.org/bot123/sendMessage",
            json={
                "chat_id": "chat123",
                "text": notifier._format_telegram_message(sample_alert),
                "parse_mode": "HTML"
            }
        )

@pytest.mark.asyncio
async def test_send_email_alert(notifier, sample_alert):
    """Test sending email alert."""
    with patch("langchain_jenkins.webhooks.notifier.config") as mock_config:
        mock_config.email.smtp_host = "smtp.example.com"
        mock_config.email.sender = "jenkins@example.com"
        mock_config.email.recipients = ["admin@example.com"]
        
        subject, body = notifier._format_email_message(sample_alert)
        
        await notifier._send_email_alert(sample_alert)
        
        notifier.http.post.assert_called_once_with(
            "http://smtp.example.com/send",
            json={
                "from": "jenkins@example.com",
                "to": ["admin@example.com"],
                "subject": subject,
                "text": body
            }
        )

def test_format_slack_message(notifier, sample_alert):
    """Test Slack message formatting."""
    message = notifier._format_slack_message(sample_alert)
    
    assert "blocks" in message
    assert "attachments" in message
    assert message["attachments"][0]["color"] == "#FFA500"  # high severity
    
    blocks = message["blocks"]
    assert blocks[0]["text"]["text"] == "🚨 Jenkins Alert"
    assert "test-job" in blocks[2]["fields"][0]["text"]
    assert "#123" in blocks[2]["fields"][1]["text"]
    assert "FAILURE" in blocks[2]["fields"][2]["text"]

def test_format_telegram_message(notifier, sample_alert):
    """Test Telegram message formatting."""
    message = notifier._format_telegram_message(sample_alert)
    
    assert "🟠" in message  # high severity
    assert "<b>Jenkins Alert</b>" in message
    assert "test-job" in message
    assert "#123" in message
    assert "FAILURE" in message
    assert "http://jenkins/job/test-job/123/" in message

def test_format_email_message(notifier, sample_alert):
    """Test email message formatting."""
    subject, body = notifier._format_email_message(sample_alert)
    
    assert "[Jenkins HIGH]" in subject
    assert "test-job" in subject
    assert "#123" in subject
    assert "FAILURE" in subject
    
    assert "Jenkins Alert" in body
    assert "test-job" in body
    assert "#123" in body
    assert "FAILURE" in body
    assert "http://jenkins/job/test-job/123/" in body
    assert "Severity: High" in body