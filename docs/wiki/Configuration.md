# Configuration Guide

This guide explains how to configure the Jenkins LangChain Agent System for your environment.

## Environment Variables

The system uses environment variables for configuration. Create a `.env` file in the root directory:

```bash
# Jenkins Configuration
JENKINS_URL=http://your-jenkins-server:8080
JENKINS_USER=your-username
JENKINS_API_TOKEN=your-api-token
JENKINS_VERIFY_SSL=true

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your-redis-password
REDIS_DB=0

# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=jenkins_agent
MONGODB_USER=your-mongodb-user
MONGODB_PASSWORD=your-mongodb-password

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
LOG_FILE=jenkins_agent.log

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false
API_SECRET_KEY=your-secret-key

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Monitoring
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
```

## Configuration Classes

The system uses Pydantic models for configuration management:

```python
# config.py
from pydantic import BaseModel, Field

class JenkinsConfig(BaseModel):
    url: str
    user: str
    api_token: str
    verify_ssl: bool = True

class LLMConfig(BaseModel):
    model: str
    temperature: float
    api_base: str
    api_key: str

class RedisConfig(BaseModel):
    url: str
    password: str = None
    db: int = 0

class MongoDBConfig(BaseModel):
    url: str
    database: str
    user: str = None
    password: str = None

class APIConfig(BaseModel):
    host: str
    port: int
    debug: bool
    secret_key: str

class Config(BaseModel):
    jenkins: JenkinsConfig
    llm: LLMConfig
    redis: RedisConfig
    mongodb: MongoDBConfig
    api: APIConfig
```

## Jenkins Configuration

### API Token Generation

1. Log in to Jenkins
2. Click your username → Configure
3. Click "Add new Token"
4. Give it a name and copy the token
5. Add to `.env`:
   ```bash
   JENKINS_API_TOKEN=your-token
   ```

### SSL Verification

For self-signed certificates:
```bash
# Disable SSL verification (not recommended for production)
JENKINS_VERIFY_SSL=false
```

## OpenAI Configuration

### API Key Setup

1. Get your API key from OpenAI
2. Add to `.env`:
   ```bash
   OPENAI_API_KEY=your-key
   ```

### Model Selection

Available models:
- `gpt-4` (recommended)
- `gpt-3.5-turbo`
- `text-davinci-003`

```bash
OPENAI_MODEL=gpt-4
```

## Redis Configuration

### Basic Setup

```bash
REDIS_URL=redis://localhost:6379
```

### Authentication

```bash
REDIS_PASSWORD=your-password
```

### Multiple Databases

```bash
REDIS_DB=1  # Use database 1
```

## MongoDB Configuration

### Connection URL

```bash
MONGODB_URL=mongodb://localhost:27017
```

### Authentication

```bash
MONGODB_USER=your-user
MONGODB_PASSWORD=your-password
```

### Database Selection

```bash
MONGODB_DATABASE=jenkins_agent
```

## API Configuration

### Server Settings

```bash
API_HOST=0.0.0.0
API_PORT=8000
```

### Security

```bash
API_SECRET_KEY=your-secret-key
```

### Debug Mode

```bash
API_DEBUG=true
```

## Rate Limiting

### Basic Configuration

```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### Custom Rules

```python
# rate_limit.py
RATE_LIMIT_RULES = {
    "default": "100/minute",
    "build": "10/minute",
    "plugin": "5/minute"
}
```

## Monitoring

### Prometheus Integration

```bash
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
```

### Custom Metrics

```python
# monitoring.py
from prometheus_client import Counter, Gauge, Histogram

BUILD_DURATION = Histogram(
    "jenkins_build_duration_seconds",
    "Build duration in seconds",
    ["job_name"]
)

BUILD_SUCCESS = Counter(
    "jenkins_build_success_total",
    "Total successful builds",
    ["job_name"]
)
```

## Logging

### Log Levels

Available levels:
- `DEBUG`
- `INFO`
- `WARNING`
- `ERROR`
- `CRITICAL`

```bash
LOG_LEVEL=INFO
```

### Log Format

```bash
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### Log File

```bash
LOG_FILE=jenkins_agent.log
```

## Advanced Configuration

### Custom Agent Configuration

```python
# agent_config.py
AGENT_CONFIG = {
    "build": {
        "max_retries": 3,
        "timeout": 300
    },
    "log": {
        "max_log_size": 1048576,
        "analysis_timeout": 60
    }
}
```

### Cache Configuration

```python
# cache_config.py
CACHE_CONFIG = {
    "default_ttl": 300,
    "max_size": 1000,
    "eviction_policy": "lru"
}
```

### Security Configuration

```python
# security_config.py
SECURITY_CONFIG = {
    "allowed_origins": ["http://localhost:3000"],
    "max_token_age": 3600,
    "require_https": True
}
```

## Environment-Specific Configuration

### Development

```bash
# .env.development
API_DEBUG=true
LOG_LEVEL=DEBUG
```

### Production

```bash
# .env.production
API_DEBUG=false
LOG_LEVEL=INFO
REQUIRE_HTTPS=true
```

### Testing

```bash
# .env.test
MONGODB_DATABASE=jenkins_agent_test
REDIS_DB=1
```

## Configuration Validation

The system validates configuration on startup:

```python
def validate_config():
    try:
        config = Config()
        config.validate()
        return config
    except ValidationError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
```

## Troubleshooting

### Common Issues

1. **Jenkins Connection**
   ```bash
   # Test Jenkins connection
   curl -u $JENKINS_USER:$JENKINS_API_TOKEN $JENKINS_URL/api/json
   ```

2. **Redis Connection**
   ```bash
   # Test Redis connection
   redis-cli -u $REDIS_URL ping
   ```

3. **MongoDB Connection**
   ```bash
   # Test MongoDB connection
   mongosh $MONGODB_URL
   ```

### Configuration Testing

```python
# test_config.py
async def test_config():
    config = Config()
    
    # Test Jenkins connection
    jenkins = JenkinsAPI()
    assert await jenkins.test_connection()
    
    # Test Redis connection
    redis = Redis()
    assert await redis.ping()
    
    # Test MongoDB connection
    mongo = MongoDB()
    assert await mongo.test_connection()
```