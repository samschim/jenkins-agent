"""Notification service for Jenkins alerts."""
from typing import Dict, Any, Optional, List
import json
import asyncio
import httpx
from redis.asyncio import Redis
from ..config.config import config
from ..utils.error_handler import handle_errors

class NotificationService:
    """Service for sending notifications."""
    
    def __init__(self):
        """Initialize notification service."""
        self.redis = Redis.from_url(config.redis.url)
        self.http = httpx.AsyncClient()
    
    async def start(self) -> None:
        """Start notification service."""
        try:
            # Subscribe to Redis alerts channel
            pubsub = self.redis.pubsub()
            await pubsub.subscribe("jenkins_alerts")
            
            # Process messages
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await self._process_alert(message["data"])
        finally:
            await self.http.aclose()
    
    @handle_errors()
    async def _process_alert(self, data: str) -> None:
        """Process alert message.
        
        Args:
            data: Alert message data
        """
        alert = json.loads(data)
        
        # Send notifications based on severity
        severity = alert.get("severity", "low")
        
        if severity == "critical":
            await asyncio.gather(
                self._send_slack_alert(alert),
                self._send_telegram_alert(alert),
                self._send_email_alert(alert)
            )
        elif severity == "high":
            await asyncio.gather(
                self._send_slack_alert(alert),
                self._send_telegram_alert(alert)
            )
        else:
            await self._send_slack_alert(alert)
    
    async def _send_slack_alert(self, alert: Dict[str, Any]) -> None:
        """Send alert to Slack.
        
        Args:
            alert: Alert data
        """
        if not config.slack.webhook_url:
            return
        
        # Create Slack message
        message = self._format_slack_message(alert)
        
        # Send to Slack
        await self.http.post(
            config.slack.webhook_url,
            json=message
        )
    
    async def _send_telegram_alert(self, alert: Dict[str, Any]) -> None:
        """Send alert to Telegram.
        
        Args:
            alert: Alert data
        """
        if not (config.telegram.bot_token and config.telegram.chat_id):
            return
        
        # Create Telegram message
        message = self._format_telegram_message(alert)
        
        # Send to Telegram
        await self.http.post(
            f"https://api.telegram.org/bot{config.telegram.bot_token}/sendMessage",
            json={
                "chat_id": config.telegram.chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
        )
    
    async def _send_email_alert(self, alert: Dict[str, Any]) -> None:
        """Send alert via email.
        
        Args:
            alert: Alert data
        """
        if not (config.email.smtp_host and config.email.recipients):
            return
        
        # Create email message
        subject, body = self._format_email_message(alert)
        
        # Send email using SMTP
        message = {
            "from": config.email.sender,
            "to": config.email.recipients,
            "subject": subject,
            "text": body
        }
        
        # Send to email service
        await self.http.post(
            f"http://{config.email.smtp_host}/send",
            json=message
        )
    
    def _format_slack_message(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Format alert for Slack.
        
        Args:
            alert: Alert data
            
        Returns:
            Slack message
        """
        event = alert["event"]
        severity = alert["severity"]
        
        # Set color based on severity
        colors = {
            "critical": "#FF0000",
            "high": "#FFA500",
            "medium": "#FFFF00",
            "low": "#00FF00"
        }
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 Jenkins Alert"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": alert["message"]
                }
            }
        ]
        
        # Add event details
        if event["type"] == "build":
            blocks.extend([
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Job:* {event['job_name']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Build:* #{event['build_number']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Status:* {event['status']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Duration:* {event['duration']}s"
                        }
                    ]
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View Build"
                            },
                            "url": event["url"]
                        }
                    ]
                }
            ])
        
        return {
            "blocks": blocks,
            "attachments": [
                {
                    "color": colors.get(severity, "#808080"),
                    "footer": f"Severity: {severity.title()}"
                }
            ]
        }
    
    def _format_telegram_message(self, alert: Dict[str, Any]) -> str:
        """Format alert for Telegram.
        
        Args:
            alert: Alert data
            
        Returns:
            Telegram message
        """
        event = alert["event"]
        severity = alert["severity"]
        
        # Set emoji based on severity
        emojis = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢"
        }
        
        message = [
            f"{emojis.get(severity, '⚪')} <b>Jenkins Alert</b>",
            "",
            alert["message"]
        ]
        
        # Add event details
        if event["type"] == "build":
            message.extend([
                "",
                "<b>Details:</b>",
                f"• Job: {event['job_name']}",
                f"• Build: #{event['build_number']}",
                f"• Status: {event['status']}",
                f"• Duration: {event['duration']}s",
                "",
                f"<a href='{event['url']}'>View Build</a>"
            ])
        
        return "\n".join(message)
    
    def _format_email_message(
        self,
        alert: Dict[str, Any]
    ) -> tuple[str, str]:
        """Format alert for email.
        
        Args:
            alert: Alert data
            
        Returns:
            Email subject and body
        """
        event = alert["event"]
        severity = alert["severity"]
        
        # Create subject
        if event["type"] == "build":
            subject = (
                f"[Jenkins {severity.upper()}] "
                f"Build {event['job_name']} #{event['build_number']} "
                f"{event['status']}"
            )
        else:
            subject = f"[Jenkins {severity.upper()}] {alert['message']}"
        
        # Create body
        body = [
            "Jenkins Alert",
            "============",
            "",
            alert["message"],
            "",
            "Details:",
            "--------"
        ]
        
        if event["type"] == "build":
            body.extend([
                f"Job: {event['job_name']}",
                f"Build: #{event['build_number']}",
                f"Status: {event['status']}",
                f"Duration: {event['duration']}s",
                f"URL: {event['url']}"
            ])
        
        body.extend([
            "",
            f"Severity: {severity.title()}",
            f"Timestamp: {alert['timestamp']}"
        ])
        
        return subject, "\n".join(body)

# Global instance
notifier = NotificationService()