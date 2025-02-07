# Phase 3: Error Handling, Caching, and Testing

## Overview
Phase 3 adds robust error handling, caching system, and comprehensive testing to the LangChain Jenkins Agent system.

## New Components

### 1. Error Handling
#### Error Module (`errors.py`)
- Custom exception classes
- Error handling decorator
- Response validation
- Retry mechanism

#### Features
- Structured error responses
- Automatic retries
- Detailed error logging
- Context preservation

### 2. Caching System
#### Cache Module (`cache.py`)
- Redis-based caching
- Key generation
- TTL management
- Cache decorators

#### Features
- Response caching
- Automatic key generation
- Pattern-based cache clearing
- Configurable TTL

### 3. Testing Suite
#### Unit Tests
- Cache system tests
- Error handling tests
- Agent tests
- Tool tests

#### Integration Tests
- Jenkins API tests
- Agent integration tests
- End-to-end workflows

## Implementation Details

### Error Handling
1. **Custom Exceptions**
   ```python
   class JenkinsError(Exception):
       def __init__(self, message, status_code=None, details=None):
           super().__init__(message)
           self.status_code = status_code
           self.details = details or {}
   ```

2. **Error Handler Decorator**
   ```python
   @error_handler
   async def jenkins_operation():
       # Operation that might fail
       pass
   ```

3. **Retry Mechanism**
   ```python
   @retry_on_error(max_retries=3, delay=1.0)
   async def retry_operation():
       # Operation that might need retries
       pass
   ```

### Caching System
1. **Cache Manager**
   ```python
   cache = CacheManager()
   
   @cache.cached("jobs", ttl=300)
   async def get_job_info(job_name):
       # Get job info from Jenkins
       pass
   ```

2. **Cache Operations**
   ```python
   # Get/set values
   value = await cache.get(key)
   await cache.set(key, value, ttl=300)
   
   # Clear cache
   await cache.clear_pattern("jobs:*")
   ```

### Testing Suite
1. **Unit Tests**
   ```bash
   # Run unit tests
   pytest tests/unit/
   
   # Run with coverage
   pytest --cov=langchain_jenkins tests/unit/
   ```

2. **Integration Tests**
   ```bash
   # Run integration tests
   pytest tests/integration/
   
   # Run specific test
   pytest tests/integration/test_agents.py
   ```

## Usage Examples

### Error Handling
```python
from langchain_jenkins.utils.errors import error_handler, retry_on_error

@error_handler
@retry_on_error(max_retries=3)
async def safe_operation():
    result = await jenkins_api.get_job_info("my-job")
    return result
```

### Caching
```python
from langchain_jenkins.utils.cache import cache

@cache.cached("builds", ttl=600)
async def get_build_info(build_id):
    return await jenkins_api.get_build_info(build_id)
```

### Testing
```python
# Run all tests
pytest

# Run with specific markers
pytest -m "unit"
pytest -m "integration"

# Run with coverage report
pytest --cov=langchain_jenkins --cov-report=html
```

## Configuration

### Error Handling
```python
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure retry settings
RETRY_MAX_ATTEMPTS = 3
RETRY_DELAY = 1.0
```

### Caching
```python
# Redis configuration
REDIS_URL = "redis://localhost:6379"
DEFAULT_TTL = 300  # 5 minutes
```

### Testing
```ini
# pytest.ini
[pytest]
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Tests that take a long time to run
```

## Next Steps
1. Add performance monitoring
2. Implement rate limiting
3. Add more test scenarios
4. Enhance error recovery
5. Improve cache efficiency