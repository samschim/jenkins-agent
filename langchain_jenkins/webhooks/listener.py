"""Webhook listener for Jenkins events."""
from typing import Dict, Any, Optional
from datetime import datetime
import json
from fastapi import FastAPI, Request, HTTPException
from redis.asyncio import Redis
from ..config.config import config
from ..utils.error_handler import handle_errors
from ..db.mongo_client import mongo_client

app = FastAPI(
    title="Jenkins Webhook Listener",
    description="Webhook listener for Jenkins events",
    version="1.0.0"
)

# Redis client for event queue
redis = Redis.from_url(config.redis.url)

@app.post("/webhook")
@handle_errors()
async def jenkins_webhook(request: Request) -> Dict[str, Any]:
    """Handle Jenkins webhook events.
    
    Args:
        request: FastAPI request
        
    Returns:
        Webhook response
    """
    try:
        payload = await request.json()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON payload: {str(e)}"
        )
    
    # Extract event data
    event = _parse_event(payload)
    
    # Store event in Redis queue
    await redis.lpush(
        "jenkins_events",
        json.dumps(event)
    )
    
    # Store in MongoDB if it's a build event
    if event["type"] == "build":
        await _store_build_event(event)
    
    # Publish alerts if needed
    if _should_alert(event):
        await _publish_alert(event)
    
    return {
        "status": "success",
        "message": "Webhook received",
        "event": event
    }

def _parse_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Jenkins webhook payload.
    
    Args:
        payload: Webhook payload
        
    Returns:
        Parsed event
    """
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "raw_payload": payload
    }
    
    # Determine event type
    if "build" in payload:
        event["type"] = "build"
        event.update(_parse_build_event(payload["build"]))
    elif "scm" in payload:
        event["type"] = "scm"
        event.update(_parse_scm_event(payload["scm"]))
    else:
        event["type"] = "unknown"
    
    return event

def _parse_build_event(build: Dict[str, Any]) -> Dict[str, Any]:
    """Parse build event data.
    
    Args:
        build: Build event data
        
    Returns:
        Parsed build event
    """
    return {
        "job_name": build.get("full_url", "").split("/")[-3],
        "build_number": build.get("number"),
        "status": build.get("status", "UNKNOWN"),
        "phase": build.get("phase", "UNKNOWN"),
        "duration": build.get("duration", 0),
        "url": build.get("full_url"),
        "parameters": build.get("parameters", {}),
        "artifacts": [
            {
                "name": a.get("fileName"),
                "path": a.get("relativePath"),
                "url": a.get("url")
            }
            for a in build.get("artifacts", [])
        ]
    }

def _parse_scm_event(scm: Dict[str, Any]) -> Dict[str, Any]:
    """Parse SCM event data.
    
    Args:
        scm: SCM event data
        
    Returns:
        Parsed SCM event
    """
    return {
        "url": scm.get("url"),
        "branch": scm.get("branch"),
        "commit": scm.get("commit"),
        "changes": [
            {
                "file": c.get("file"),
                "author": c.get("author", {}).get("name"),
                "message": c.get("message")
            }
            for c in scm.get("changes", [])
        ]
    }

def _should_alert(event: Dict[str, Any]) -> bool:
    """Check if event should trigger an alert.
    
    Args:
        event: Event data
        
    Returns:
        True if alert should be sent
    """
    if event["type"] == "build":
        # Alert on build failures
        if event["status"] == "FAILURE":
            return True
        
        # Alert on long-running builds
        if event["duration"] > config.alerts.max_build_duration:
            return True
        
        # Alert on specific job failures
        if (
            event["job_name"] in config.alerts.critical_jobs
            and event["status"] != "SUCCESS"
        ):
            return True
    
    return False

async def _publish_alert(event: Dict[str, Any]) -> None:
    """Publish alert to Redis channel.
    
    Args:
        event: Event data
    """
    alert = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": "jenkins_alert",
        "event": event,
        "severity": _get_alert_severity(event)
    }
    
    # Add alert message
    if event["type"] == "build":
        alert["message"] = (
            f"🚨 Build failure in {event['job_name']} #{event['build_number']}\n"
            f"Status: {event['status']}\n"
            f"URL: {event['url']}"
        )
    
    # Publish to Redis
    await redis.publish(
        "jenkins_alerts",
        json.dumps(alert)
    )

def _get_alert_severity(event: Dict[str, Any]) -> str:
    """Get alert severity level.
    
    Args:
        event: Event data
        
    Returns:
        Severity level
    """
    if event["type"] == "build":
        # Critical severity for critical jobs
        if event["job_name"] in config.alerts.critical_jobs:
            return "critical"
        
        # High severity for failures
        if event["status"] == "FAILURE":
            return "high"
        
        # Medium severity for warnings
        if event["status"] == "UNSTABLE":
            return "medium"
    
    return "low"

async def _store_build_event(event: Dict[str, Any]) -> None:
    """Store build event in MongoDB.
    
    Args:
        event: Event data
    """
    # Store build log
    if "url" in event:
        await mongo_client.store_build_log(
            str(event["build_number"]),
            event["job_name"],
            f"Build log for {event['job_name']} #{event['build_number']}",
            {
                "status": event["status"],
                "phase": event["phase"],
                "duration": event["duration"],
                "url": event["url"]
            }
        )
    
    # Store error if build failed
    if event["status"] == "FAILURE":
        await mongo_client.store_build_error(
            str(event["build_number"]),
            event["job_name"],
            "build_failure",
            f"Build {event['job_name']} #{event['build_number']} failed",
            metadata={
                "phase": event["phase"],
                "duration": event["duration"],
                "url": event["url"]
            }
        )