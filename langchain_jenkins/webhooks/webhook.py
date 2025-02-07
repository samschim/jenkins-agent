"""Webhook module for Jenkins operations."""
from typing import Dict, Any, Optional
import json
import httpx
import logging
import datetime
from ..utils.errors import JenkinsError, handle_jenkins_error

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebhookHandler:
    """Handler for webhook operations."""
    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None):
        """Initialize webhook handler.
        
        Args:
            url: Webhook URL
            headers: Optional headers for webhook requests
        """
        self.url = url
        self.headers = headers or {}
        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = "application/json"

    async def send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send webhook payload.
        
        Args:
            payload: Webhook payload
            
        Returns:
            Response from webhook endpoint
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.url,
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise JenkinsError(
                f"Webhook request failed: {str(e)}",
                status_code=getattr(e.response, "status_code", None),
                details={"url": self.url, "payload": payload}
            )
        except Exception as e:
            raise JenkinsError(
                f"Webhook error: {str(e)}",
                details={"url": self.url, "payload": payload}
            )

    async def verify(self) -> bool:
        """Verify webhook endpoint is accessible.
        
        Returns:
            True if webhook endpoint is accessible
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.head(self.url)
                return response.status_code == 200
        except Exception:
            return False

    def format_payload(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format webhook payload.
        
        Args:
            event_type: Type of event
            data: Event data
            
        Returns:
            Formatted webhook payload
        """
        return {
            "event": event_type,
            "data": data,
            "timestamp": str(datetime.datetime.now(datetime.UTC))
        }

    async def notify(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send webhook notification.
        
        Args:
            event_type: Type of event
            data: Event data
            
        Returns:
            Response from webhook endpoint
        """
        payload = self.format_payload(event_type, data)
        try:
            return await self.send(payload)
        except Exception as e:
            context = {
                "event_type": event_type,
                "webhook_url": self.url
            }
            return handle_jenkins_error(e, context)

class WebhookNotifier:
    """Notifier for webhook operations."""
    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None):
        """Initialize webhook notifier.
        
        Args:
            url: Webhook URL
            headers: Optional headers for webhook requests
        """
        self.handler = WebhookHandler(url, headers)

    async def send_notification(self, message: str, **kwargs) -> Dict[str, Any]:
        """Send notification.
        
        Args:
            message: Notification message
            **kwargs: Additional notification data
            
        Returns:
            Response from webhook endpoint
        """
        data = {
            "message": message,
            **kwargs
        }
        return await self.handler.notify("notification", data)

    async def send_alert(self, alert_type: str, message: str, **kwargs) -> Dict[str, Any]:
        """Send alert.
        
        Args:
            alert_type: Type of alert
            message: Alert message
            **kwargs: Additional alert data
            
        Returns:
            Response from webhook endpoint
        """
        data = {
            "alert_type": alert_type,
            "message": message,
            **kwargs
        }
        return await self.handler.notify("alert", data)