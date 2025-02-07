# API Reference

This document provides detailed information about the Jenkins LangChain Agent system's APIs.

## 🌐 REST API

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication
```http
Authorization: Bearer your-token-here
```

### Endpoints

#### Tasks

##### Create Task
```http
POST /tasks
Content-Type: application/json

{
    "task": "Create a new pipeline for Python project",
    "parameters": {
        "project_type": "python",
        "with_tests": true
    }
}
```

Response:
```json
{
    "status": "success",
    "task_id": "task-123",
    "result": {
        "pipeline": "...",
        "message": "Pipeline created successfully"
    }
}
```

##### Get Task Status
```http
GET /tasks/{task_id}
```

Response:
```json
{
    "status": "completed",
    "result": {
        "pipeline": "...",
        "message": "Pipeline created successfully"
    }
}
```

#### Pipelines

##### Create Pipeline
```http
POST /pipelines
Content-Type: application/json

{
    "name": "my-pipeline",
    "type": "python",
    "config": {
        "with_tests": true,
        "with_deploy": false
    }
}
```

Response:
```json
{
    "status": "success",
    "pipeline_id": "pipe-123",
    "config": "..."
}
```

##### Get Pipeline
```http
GET /pipelines/{pipeline_id}
```

Response:
```json
{
    "id": "pipe-123",
    "name": "my-pipeline",
    "status": "active",
    "config": "...",
    "last_build": {
        "number": 42,
        "status": "success"
    }
}
```

##### Update Pipeline
```http
PUT /pipelines/{pipeline_id}
Content-Type: application/json

{
    "config": {
        "with_tests": true,
        "with_deploy": true
    }
}
```

Response:
```json
{
    "status": "success",
    "message": "Pipeline updated"
}
```

#### Builds

##### Trigger Build
```http
POST /builds
Content-Type: application/json

{
    "pipeline_id": "pipe-123",
    "parameters": {
        "branch": "main",
        "environment": "staging"
    }
}
```

Response:
```json
{
    "status": "success",
    "build_number": 42,
    "url": "..."
}
```

##### Get Build Status
```http
GET /builds/{build_id}
```

Response:
```json
{
    "id": "build-123",
    "number": 42,
    "status": "success",
    "duration": 123,
    "url": "...",
    "artifacts": [
        {
            "name": "app.jar",
            "url": "..."
        }
    ]
}
```

#### Metrics

##### Get System Metrics
```http
GET /metrics
```

Response:
```json
{
    "builds": {
        "total": 1234,
        "success_rate": 98.5,
        "average_duration": 123
    },
    "pipelines": {
        "total": 42,
        "active": 35
    },
    "resources": {
        "cpu_usage": 45.2,
        "memory_usage": 78.3
    }
}
```

##### Get Pipeline Metrics
```http
GET /metrics/pipelines/{pipeline_id}
```

Response:
```json
{
    "success_rate": 98.5,
    "average_duration": 123,
    "last_builds": [
        {
            "number": 42,
            "status": "success",
            "duration": 120
        }
    ]
}
```

## 🐍 Python API

### Supervisor Agent

```python
from langchain_jenkins.agents.supervisor import SupervisorAgent

# Initialize
supervisor = SupervisorAgent()

# Handle task
result = await supervisor.handle_task(
    "Create a new pipeline for Python project"
)

# Handle complex task
result = await supervisor.handle_complex_task(
    "Create pipeline and analyze its first build"
)

# Get metrics
metrics = await supervisor.collect_metrics_and_insights()
```

### Pipeline Manager

```python
from langchain_jenkins.agents.enhanced_pipeline_manager import (
    EnhancedPipelineManager
)

# Initialize
pipeline_manager = EnhancedPipelineManager()

# Create pipeline
result = await pipeline_manager.handle_task(
    "Create a new pipeline for Java project with testing"
)

# Optimize pipeline
result = await pipeline_manager.handle_task(
    "Optimize my-pipeline for better performance"
)

# Scan security
result = await pipeline_manager.handle_task(
    "Scan my-pipeline for security issues"
)
```

### Build Manager

```python
from langchain_jenkins.agents.enhanced_build_manager import (
    EnhancedBuildManager
)

# Initialize
build_manager = EnhancedBuildManager()

# Create build
result = await build_manager.handle_task(
    "Create a new build job named my-project"
)

# Trigger build
result = await build_manager.handle_task(
    "Start build for my-project"
)

# Analyze build
result = await build_manager.handle_task(
    "Analyze build performance for my-project"
)
```

### Log Analyzer

```python
from langchain_jenkins.agents.enhanced_log_analyzer import (
    EnhancedLogAnalyzer
)

# Initialize
log_analyzer = EnhancedLogAnalyzer()

# Analyze logs
result = await log_analyzer.handle_task(
    "Analyze build logs for my-project"
)

# Find patterns
result = await log_analyzer.handle_task(
    "Find error patterns in my-project builds"
)

# Get recommendations
result = await log_analyzer.handle_task(
    "Get optimization recommendations for my-project"
)
```

## 🔧 Configuration API

### Environment Variables

```python
from langchain_jenkins.config import config

# Get configuration
jenkins_url = config.jenkins.url
api_token = config.jenkins.api_token

# Get secret
secret = config.get_secret("API_KEY")

# Update configuration
config.update({
    "jenkins": {
        "url": "http://new-jenkins:8080"
    }
})
```

### Custom Configuration

```python
from langchain_jenkins.config import Config

# Create custom configuration
custom_config = Config(
    jenkins={
        "url": "http://jenkins:8080",
        "user": "admin",
        "api_token": "token"
    },
    openai={
        "api_key": "key",
        "model": "gpt-4"
    }
)

# Use custom configuration
supervisor = SupervisorAgent(config=custom_config)
```

## 📊 Metrics API

### Collecting Metrics

```python
from langchain_jenkins.utils.metrics import MetricsCollector

# Initialize
collector = MetricsCollector()

# Collect metrics
metrics = await collector.collect_metrics()

# Get specific metrics
build_metrics = await collector.collect_build_metrics()
pipeline_metrics = await collector.collect_pipeline_metrics()

# Generate insights
insights = await collector.generate_insights(metrics)
```

### Custom Metrics

```python
from langchain_jenkins.utils.metrics import metrics

# Timer decorator
@metrics.timer("operation_duration")
async def operation():
    # Operation code
    pass

# Counter
@metrics.counter("operation_count")
async def counted_operation():
    # Operation code
    pass

# Gauge
@metrics.gauge("queue_size")
def get_queue_size():
    return len(queue)
```

## 🔒 Security API

### Pipeline Security

```python
from langchain_jenkins.tools.pipeline_security import SecurityScanner

# Initialize
scanner = SecurityScanner()

# Scan pipeline
results = await scanner.scan_pipeline(pipeline_config)

# Secure pipeline
secured = await scanner.secure_pipeline(pipeline_config)

# Validate security
validation = await scanner.validate_security(pipeline_config)
```

### Authentication

```python
from langchain_jenkins.utils.auth import (
    create_token,
    validate_token,
    require_auth
)

# Create token
token = create_token(user_id="user123")

# Validate token
is_valid = validate_token(token)

# Protect endpoint
@require_auth
async def protected_endpoint():
    # Protected code
    pass
```

## 🔄 Webhook API

### Webhook Management

```python
from langchain_jenkins.utils.webhook import WebhookManager

# Initialize
webhook_manager = WebhookManager()

# Register webhook
webhook_id = await webhook_manager.register(
    url="https://example.com/webhook",
    events=["build.complete", "pipeline.start"]
)

# Send notification
await webhook_manager.notify(
    webhook_id,
    event="build.complete",
    data={"build_id": "123"}
)

# Remove webhook
await webhook_manager.unregister(webhook_id)
```

### Event Handling

```python
from langchain_jenkins.utils.webhook import event_handler

# Handle event
@event_handler("build.complete")
async def handle_build_complete(data: dict):
    build_id = data["build_id"]
    # Handle build completion
    pass
```