# Development Guide

This guide provides information for developers who want to contribute to or extend the Jenkins LangChain Agent system.

## 🔧 Development Setup

### Prerequisites
- Python 3.8+
- Poetry for dependency management
- Docker and Docker Compose
- Jenkins server (local or remote)
- MongoDB
- Redis

### Local Development Environment

1. Clone the repository:
```bash
git clone https://github.com/samschim/jenkins-agent.git
cd jenkins-agent
```

2. Install dependencies:
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install
```

3. Set up pre-commit hooks:
```bash
poetry run pre-commit install
```

4. Configure environment:
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
vim .env
```

5. Start development services:
```bash
# Start MongoDB and Redis
docker-compose -f docker-compose.dev.yml up -d

# Start development server
poetry run python -m langchain_jenkins.web.app --debug
```

## 🏗️ Project Structure

```
langchain_jenkins/
├── agents/                 # Agent implementations
│   ├── base_agent.py      # Base agent class
│   ├── supervisor.py      # Supervisor agent
│   └── specialized/       # Specialized agents
├── tools/                 # Agent tools
│   ├── jenkins_api.py     # Jenkins API wrapper
│   └── pipeline_tools.py  # Pipeline management tools
├── utils/                 # Utility functions
│   ├── embeddings.py      # Embedding utilities
│   └── metrics.py         # Metrics collection
├── web/                   # Web interface
│   ├── app.py            # FastAPI application
│   └── frontend/         # React frontend
├── cli/                  # Command-line interface
│   ├── jenkins_cli.py    # CLI implementation
│   └── interactive.py    # Interactive mode
└── config/               # Configuration
    └── config.py         # Configuration management
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run specific test suite
poetry run pytest tests/unit/
poetry run pytest tests/integration/

# Run with coverage
poetry run pytest --cov=langchain_jenkins

# Generate coverage report
poetry run coverage html
```

### Writing Tests

1. Unit Tests:
```python
import pytest
from langchain_jenkins.agents.supervisor import SupervisorAgent

@pytest.mark.asyncio
async def test_task_routing():
    supervisor = SupervisorAgent()
    result = await supervisor.handle_task("Create pipeline")
    assert result["status"] == "success"
```

2. Integration Tests:
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_pipeline_creation():
    supervisor = SupervisorAgent()
    result = await supervisor.handle_task(
        "Create Python pipeline with testing"
    )
    assert "pipeline" in result
```

## 🔄 Development Workflow

### 1. Feature Development

1. Create feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make changes and test:
```bash
# Run tests
poetry run pytest

# Format code
poetry run black .
poetry run isort .

# Check types
poetry run mypy .
```

3. Commit changes:
```bash
git add .
git commit -m "feat: Add your feature"
```

### 2. Code Quality

1. Code Style:
- Follow PEP 8
- Use type hints
- Write docstrings (Google style)
- Keep functions focused

2. Example:
```python
from typing import Dict, Any

async def process_task(task: str) -> Dict[str, Any]:
    """Process a task and return results.
    
    Args:
        task: Task description
        
    Returns:
        Dictionary with task results
        
    Raises:
        ValueError: If task is invalid
    """
    if not task:
        raise ValueError("Task cannot be empty")
    
    # Process task
    return {"status": "success", "result": "..."}
```

### 3. Documentation

1. Code Documentation:
- Document all public functions and classes
- Include examples in docstrings
- Explain complex algorithms

2. Wiki Documentation:
- Update relevant wiki pages
- Add new features to docs
- Include code examples

## 🔌 Extending the System

### 1. Adding New Agents

1. Create agent class:
```python
from langchain_jenkins.agents.base_agent import BaseAgent

class NewAgent(BaseAgent):
    """New specialized agent."""
    
    def __init__(self):
        tools = [
            Tool(name="tool1", func=self._tool1),
            Tool(name="tool2", func=self._tool2)
        ]
        super().__init__(tools)
    
    async def handle_task(self, task: str) -> Dict[str, Any]:
        """Handle specialized tasks."""
        return await self.execute_task(task)
```

2. Register with supervisor:
```python
class SupervisorAgent:
    def __init__(self):
        self.agents = {
            "new": NewAgent(),
            # ... other agents
        }
```

### 2. Adding New Tools

1. Create tool function:
```python
from langchain.tools import Tool

async def new_tool(input_str: str) -> str:
    """Tool description."""
    # Implement tool logic
    return "Result"

# Add to agent
tools = [
    Tool(
        name="NewTool",
        func=new_tool,
        description="Tool description"
    )
]
```

### 3. Adding New Features

1. Plan the feature:
   - Define requirements
   - Design API
   - Plan testing strategy

2. Implement feature:
   - Write tests first
   - Implement feature
   - Document changes

3. Test thoroughly:
   - Unit tests
   - Integration tests
   - Performance tests

## 🔒 Security Guidelines

1. Credential Handling:
```python
# Good
from langchain_jenkins.config import config
api_key = config.get_secret("API_KEY")

# Bad
api_key = "hardcoded-secret"
```

2. Input Validation:
```python
def process_input(data: str) -> None:
    # Validate input
    if not isinstance(data, str):
        raise TypeError("Input must be string")
    if len(data) > 1000:
        raise ValueError("Input too long")
    # Process data
```

3. Error Handling:
```python
try:
    result = await api.call()
except ApiError as e:
    logger.error(f"API error: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

## 📈 Performance Guidelines

1. Caching:
```python
from langchain_jenkins.utils.cache import cache

@cache(ttl=300)
async def expensive_operation() -> Dict[str, Any]:
    # Expensive computation
    return result
```

2. Async Operations:
```python
async def process_many(items: List[str]) -> List[Dict]:
    tasks = [process_one(item) for item in items]
    return await asyncio.gather(*tasks)
```

3. Resource Management:
```python
async with aiohttp.ClientSession() as session:
    async with session.get(url) as response:
        data = await response.json()
```

## 🐛 Debugging

1. Logging:
```python
import logging

logger = logging.getLogger(__name__)

async def process():
    logger.debug("Starting process")
    try:
        result = await operation()
        logger.info("Process completed")
    except Exception as e:
        logger.error(f"Process failed: {e}")
```

2. Debugging Tools:
```bash
# Run with debugger
poetry run python -m debugpy --listen 5678 --wait-for-client -m langchain_jenkins.main

# View logs
tail -f logs/jenkins_agent.log
```

## 📊 Monitoring

1. Metrics Collection:
```python
from langchain_jenkins.utils.metrics import metrics

@metrics.timer("operation_duration")
async def operation():
    # Operation code
```

2. Health Checks:
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "dependencies": {
            "jenkins": await check_jenkins(),
            "mongodb": await check_mongodb()
        }
    }
```