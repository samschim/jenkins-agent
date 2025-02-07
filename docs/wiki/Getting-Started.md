# Getting Started

This guide will help you get up and running with the Jenkins LangChain Agent System.

## Prerequisites

Before you begin, ensure you have:

1. Python 3.8 or higher installed
2. A Jenkins server with API access
3. An OpenAI API key
4. Redis server (for caching)
5. MongoDB server (for data persistence)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/samschim/jenkins-agent.git
cd jenkins-agent
```

### 2. Create a Virtual Environment

```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using conda
conda create -n jenkins-agent python=3.8
conda activate jenkins-agent
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your settings:
```bash
# Jenkins Configuration
JENKINS_URL=http://your-jenkins-server:8080
JENKINS_USER=your-username
JENKINS_API_TOKEN=your-api-token

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key

# Redis Configuration
REDIS_URL=redis://localhost:6379

# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=jenkins_agent
```

## Quick Start

### 1. Basic Usage

```python
from langchain_jenkins.agents.supervisor import SupervisorAgent

# Initialize the supervisor agent
supervisor = SupervisorAgent()

# Handle a simple task
async def main():
    result = await supervisor.handle_task(
        "Create a new build job named my-project"
    )
    print(result)

# Run the task
import asyncio
asyncio.run(main())
```

### 2. Web API

Start the web server:
```bash
python -m langchain_jenkins.web.app
```

Use the API:
```bash
# Create a new job
curl -X POST http://localhost:8000/api/v1/tasks \
    -H "Content-Type: application/json" \
    -d '{"task": "Create a new build job named my-project"}'
```

### 3. Command Line Interface

Use the CLI tool:
```bash
# Install CLI tool
pip install -e .

# Run commands
jenkins-agent create-job my-project
jenkins-agent trigger-build my-project
jenkins-agent analyze-log my-project
```

## Common Tasks

### 1. Managing Builds

```python
# Create a build job
result = await supervisor.handle_task(
    "Create a new Maven build job named my-project"
)

# Trigger a build
result = await supervisor.handle_task(
    "Start build for my-project"
)

# Check build status
result = await supervisor.handle_task(
    "Get status of my-project build"
)
```

### 2. Managing Pipelines

```python
# Create a pipeline
result = await supervisor.handle_task(
    "Create a new pipeline for Java project with build and test stages"
)

# Modify pipeline
result = await supervisor.handle_task(
    "Add deployment stage to my-pipeline"
)

# Analyze pipeline
result = await supervisor.handle_task(
    "Optimize my-pipeline for faster builds"
)
```

### 3. Analyzing Logs

```python
# Analyze build logs
result = await supervisor.handle_task(
    "Analyze the latest build log for my-project"
)

# Get error patterns
result = await supervisor.handle_task(
    "Find common errors in my-project builds"
)
```

### 4. Managing Plugins

```python
# Install plugin
result = await supervisor.handle_task(
    "Install git plugin"
)

# Update plugins
result = await supervisor.handle_task(
    "Update all plugins"
)
```

## Working with Complex Tasks

The system can handle complex tasks that require multiple agents:

```python
# Create pipeline with analysis
result = await supervisor.handle_complex_task(
    "Create a new pipeline for Java project and analyze its first build"
)

# Setup complete CI/CD
result = await supervisor.handle_complex_task(
    "Setup complete CI/CD pipeline for Python project with testing and deployment"
)
```

## Monitoring and Metrics

Get system insights:

```python
# Collect metrics
metrics = await supervisor.collect_metrics_and_insights()

# Print insights
print(f"System Health: {metrics['metrics']['health']}")
print(f"Recommendations: {metrics['recommendations']}")
```

## Error Handling

Always check task results:

```python
result = await supervisor.handle_task("Some task")
if result["status"] == "success":
    print(f"Task completed: {result['message']}")
else:
    print(f"Task failed: {result['error']}")
```

## Best Practices

1. **Task Description**
   - Be specific and clear
   - Include all necessary parameters
   - Use consistent terminology

2. **Error Handling**
   - Always check task status
   - Handle errors gracefully
   - Log errors for troubleshooting

3. **Resource Management**
   - Monitor system resources
   - Use caching appropriately
   - Clean up temporary resources

4. **Security**
   - Keep credentials secure
   - Use HTTPS for API access
   - Regularly update dependencies

## Next Steps

1. Read the [Architecture Overview](Architecture) for system details
2. Check the [Configuration Guide](Configuration) for advanced settings
3. Review [Agent Documentation](Agents) for detailed agent capabilities
4. See the [API Reference](API-Reference) for API details
5. Join our [Community](Community) for support and updates

## Troubleshooting

### Common Issues

1. **Connection Problems**
   ```python
   # Test Jenkins connection
   from langchain_jenkins.tools.jenkins_api import JenkinsAPI
   jenkins = JenkinsAPI()
   await jenkins.test_connection()
   ```

2. **Authentication Issues**
   ```python
   # Verify credentials
   from langchain_jenkins.utils.auth import verify_credentials
   await verify_credentials()
   ```

3. **Performance Issues**
   ```python
   # Check system metrics
   from langchain_jenkins.utils.monitoring import get_metrics
   metrics = await get_metrics()
   print(metrics)
   ```

### Getting Help

1. Check the [FAQ](FAQ) for common questions
2. Search [GitHub Issues](https://github.com/samschim/jenkins-agent/issues)
3. Join our [Discord Community](https://discord.gg/jenkins-agent)
4. Contact [Support](mailto:support@jenkins-agent.com)