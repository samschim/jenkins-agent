# Agent Documentation

This document provides detailed information about each agent in the system, their capabilities, and how to use them.

## Supervisor Agent

The supervisor agent is the main entry point for interacting with the system. It coordinates all other agents and provides high-level task management.

### Usage

```python
from langchain_jenkins.agents.supervisor import SupervisorAgent

# Initialize
supervisor = SupervisorAgent()

# Handle a simple task
result = await supervisor.handle_task("Create a new build job")

# Handle a complex task
result = await supervisor.handle_complex_task(
    "Create a pipeline and analyze its first build"
)

# Get system insights
insights = await supervisor.collect_metrics_and_insights()
```

### Key Methods

| Method | Description | Example |
|--------|-------------|---------|
| `handle_task()` | Handle a single task | `await supervisor.handle_task("Install git plugin")` |
| `handle_complex_task()` | Handle tasks requiring multiple agents | `await supervisor.handle_complex_task("Create pipeline and configure plugins")` |
| `collect_metrics_and_insights()` | Get system metrics and insights | `await supervisor.collect_metrics_and_insights()` |

## Build Manager Agent

The build manager agent handles all build-related operations in Jenkins.

### Usage

```python
from langchain_jenkins.agents.build_manager import BuildManagerAgent

# Initialize
build_manager = BuildManagerAgent()

# Create a new job
result = await build_manager.handle_task(
    "Create a new Maven build job named my-project"
)

# Trigger a build
result = await build_manager.handle_task(
    "Start build for my-project"
)
```

### Capabilities

- Create build jobs
- Configure build parameters
- Trigger builds
- Monitor build status
- Analyze build results

### Task Examples

```python
# Create a job
"Create a new Maven build job named my-project"

# Configure a job
"Configure my-project to use JDK 11"

# Trigger a build
"Start build for my-project"

# Get build status
"Check status of my-project build #123"
```

## Log Analyzer Agent

The log analyzer agent provides intelligent analysis of build logs and error patterns.

### Usage

```python
from langchain_jenkins.agents.log_analyzer import LogAnalyzerAgent

# Initialize
log_analyzer = LogAnalyzerAgent()

# Analyze a build log
result = await log_analyzer.handle_task(
    "Analyze the latest build log for my-project"
)
```

### Capabilities

- Error pattern detection
- Root cause analysis
- Solution recommendations
- Historical trend analysis

### Task Examples

```python
# Analyze latest build
"Analyze the latest build log for my-project"

# Find error patterns
"Find common errors in my-project builds"

# Get recommendations
"Suggest fixes for my-project build failures"
```

## Pipeline Manager Agent

The pipeline manager agent handles Jenkins pipeline operations.

### Usage

```python
from langchain_jenkins.agents.pipeline_manager import PipelineManagerAgent

# Initialize
pipeline_manager = PipelineManagerAgent()

# Create a pipeline
result = await pipeline_manager.handle_task(
    "Create a new pipeline for Java project with build and test stages"
)
```

### Capabilities

- Create pipelines
- Modify pipeline stages
- Validate pipeline syntax
- Optimize pipeline performance
- Security scanning

### Task Examples

```python
# Create pipeline
"Create a pipeline for Java project"

# Modify pipeline
"Add deployment stage to my-pipeline"

# Optimize pipeline
"Optimize my-pipeline for faster builds"
```

## Plugin Manager Agent

The plugin manager agent handles Jenkins plugin management.

### Usage

```python
from langchain_jenkins.agents.plugin_manager import PluginManagerAgent

# Initialize
plugin_manager = PluginManagerAgent()

# Install a plugin
result = await plugin_manager.handle_task(
    "Install git plugin"
)
```

### Capabilities

- Install plugins
- Update plugins
- Remove plugins
- Configure plugin settings
- Check plugin compatibility

### Task Examples

```python
# Install plugin
"Install git plugin"

# Update plugins
"Update all plugins"

# Configure plugin
"Configure git plugin with credentials"
```

## User Manager Agent

The user manager agent handles user and permission management.

### Usage

```python
from langchain_jenkins.agents.user_manager import UserManagerAgent

# Initialize
user_manager = UserManagerAgent()

# Add a user
result = await user_manager.handle_task(
    "Add new user john with developer role"
)
```

### Capabilities

- User management
- Role assignment
- Permission configuration
- Access control
- Security auditing

### Task Examples

```python
# Add user
"Add new user john"

# Assign role
"Give admin role to user john"

# Configure permissions
"Allow john to manage builds"
```

## Best Practices

1. **Task Description**
   - Be specific and clear
   - Include all necessary parameters
   - Use consistent terminology

2. **Error Handling**
   - Always check the `status` field in responses
   - Handle errors gracefully
   - Log errors for troubleshooting

3. **Performance**
   - Use batch operations when possible
   - Implement caching where appropriate
   - Monitor resource usage

4. **Security**
   - Follow principle of least privilege
   - Regularly audit permissions
   - Keep plugins updated

## Common Patterns

### Sequential Operations

```python
# Create job and trigger build
job_result = await supervisor.handle_task("Create new job my-project")
if job_result["status"] == "success":
    build_result = await supervisor.handle_task("Start build for my-project")
```

### Complex Operations

```python
# Create pipeline with plugins and analysis
result = await supervisor.handle_complex_task(
    "Create a new pipeline for Java project, install required plugins, "
    "and analyze the first build"
)
```

### Metrics Collection

```python
# Get system insights
insights = await supervisor.collect_metrics_and_insights()
print(f"System Health: {insights['metrics']['health']}")
print(f"Recommendations: {insights['recommendations']}")
```

## Troubleshooting

### Common Issues

1. **Task Routing Issues**
   - Check task description clarity
   - Verify agent availability
   - Check logs for routing decisions

2. **API Errors**
   - Verify Jenkins connectivity
   - Check API token validity
   - Review rate limits

3. **Performance Issues**
   - Monitor resource usage
   - Check caching configuration
   - Review concurrent operations

### Debug Mode

Enable debug mode for detailed logging:

```python
import logging
logging.getLogger("langchain_jenkins").setLevel(logging.DEBUG)
```