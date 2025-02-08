# Backend Development Guide

This guide provides detailed information about the backend architecture, components, and development workflow.

## 🏗️ Architecture

### Tech Stack
- Python 3.8+
- FastAPI for web API
- LangChain for AI integration
- MongoDB for data storage
- Redis for caching
- Prometheus for metrics
- Docker for containerization

### Directory Structure
```
langchain_jenkins/
├── agents/              # Agent implementations
│   ├── base_agent.py   # Base agent class
│   ├── supervisor.py   # Supervisor agent
│   └── specialized/    # Specialized agents
├── tools/              # Agent tools
│   ├── jenkins_api.py  # Jenkins API wrapper
│   └── pipeline_tools.py # Pipeline management tools
├── utils/              # Utility functions
│   ├── embeddings.py   # Embedding utilities
│   └── metrics.py      # Metrics collection
├── web/               # Web interface
│   ├── app.py         # FastAPI application
│   └── routes/        # API routes
├── cli/               # Command-line interface
│   ├── jenkins_cli.py # CLI implementation
│   └── interactive.py # Interactive mode
└── config/            # Configuration
    └── config.py      # Configuration management
```

## 🤖 Agents

### Base Agent
```python
# agents/base_agent.py
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType

class BaseAgent:
    """Base class for all agents."""
    
    def __init__(self, tools: List[Tool]):
        self.tools = tools
        self.llm = ChatOpenAI(
            model=config.llm.model,
            temperature=config.llm.temperature
        )
        self.agent = initialize_agent(
            tools=tools,
            llm=self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )
    
    async def handle_task(self, task: str) -> Dict[str, Any]:
        """Handle a task using the agent."""
        try:
            result = await self.agent.arun(task)
            return {
                "status": "success",
                "result": result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
```

### Supervisor Agent
```python
# agents/supervisor.py
class SupervisorAgent:
    """Supervisor agent that coordinates specialized agents."""
    
    def __init__(self):
        self.agents = {
            "build": EnhancedBuildManager(),
            "log": EnhancedLogAnalyzer(),
            "pipeline": EnhancedPipelineManager(),
            "plugin": EnhancedPluginManager()
        }
        self.embedding_manager = EmbeddingManager()
        self.metrics_collector = MetricsCollector()
    
    async def _determine_agent(self, task: str) -> str:
        """Determine which agent should handle a task."""
        return await self.embedding_manager.find_best_agent(task)
    
    async def handle_task(self, task: str) -> Dict[str, Any]:
        """Handle a task by routing it to the appropriate agent."""
        agent_type = await self._determine_agent(task)
        agent = self.agents[agent_type]
        return await agent.handle_task(task)
```

## 🔧 Tools

### Jenkins API
```python
# tools/jenkins_api.py
class JenkinsAPI:
    """Jenkins API wrapper."""
    
    def __init__(self):
        self.base_url = config.jenkins.url
        self.auth = (config.jenkins.user, config.jenkins.api_token)
        self.session = aiohttp.ClientSession(
            auth=aiohttp.BasicAuth(*self.auth)
        )
    
    async def get_job_info(self, job_name: str) -> Dict[str, Any]:
        """Get information about a job."""
        url = f"{self.base_url}/job/{job_name}/api/json"
        async with self.session.get(url) as response:
            return await response.json()
    
    async def create_job(
        self,
        name: str,
        config_xml: str
    ) -> Dict[str, Any]:
        """Create a new job."""
        url = f"{self.base_url}/createItem"
        params = {"name": name}
        headers = {"Content-Type": "text/xml"}
        async with self.session.post(
            url,
            params=params,
            headers=headers,
            data=config_xml
        ) as response:
            return {"status": response.status}
```

### Pipeline Tools
```python
# tools/pipeline_tools.py
class PipelineGenerator:
    """Generates Jenkins pipelines."""
    
    def __init__(self):
        self.templates = {
            "java": self._get_java_template(),
            "python": self._get_python_template(),
            "node": self._get_node_template()
        }
    
    async def generate_pipeline(
        self,
        project_type: str,
        requirements: List[str]
    ) -> Dict[str, Any]:
        """Generate a pipeline configuration."""
        template = self.templates.get(project_type)
        if not template:
            return {
                "status": "error",
                "error": f"Unsupported project type: {project_type}"
            }
        
        stages = await self._generate_stages(requirements)
        pipeline = template.format(stages=stages)
        
        return {
            "status": "success",
            "pipeline": pipeline
        }
```

## 📊 Metrics

### Metrics Collection
```python
# utils/metrics.py
class MetricsCollector:
    """Collects system metrics."""
    
    def __init__(self):
        self.build_duration = Histogram(
            'jenkins_build_duration_seconds',
            'Build duration in seconds',
            ['job_name']
        )
        self.build_success = Counter(
            'jenkins_build_success_total',
            'Total successful builds',
            ['job_name']
        )
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect system metrics."""
        return {
            "builds": await self.collect_build_metrics(),
            "pipelines": await self.collect_pipeline_metrics(),
            "resources": await self.collect_resource_metrics()
        }
```

### Prometheus Integration
```python
# web/app.py
from prometheus_client import make_asgi_app

app = FastAPI()
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.on_event("startup")
async def startup():
    """Start metrics collection."""
    metrics_collector = MetricsCollector()
    asyncio.create_task(metrics_collector.collect_metrics_loop())
```

## 🔄 WebSocket Support

### WebSocket Manager
```python
# web/websocket.py
class WebSocketManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Handle new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connections."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                self.active_connections.remove(connection)
```

### WebSocket Routes
```python
# web/routes/websocket.py
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast({
                "type": "message",
                "data": data
            })
    except WebSocketDisconnect:
        manager.active_connections.remove(websocket)
```

## 🗄️ Data Storage

### MongoDB Integration
```python
# utils/db.py
class MongoDB:
    """MongoDB client wrapper."""
    
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(
            config.mongodb.url
        )
        self.db = self.client[config.mongodb.database]
    
    async def save_build(self, build_data: Dict[str, Any]):
        """Save build data."""
        await self.db.builds.insert_one(build_data)
    
    async def get_builds(
        self,
        job_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get build history."""
        cursor = self.db.builds.find(
            {"job_name": job_name}
        ).sort("number", -1).limit(limit)
        return await cursor.to_list(length=limit)
```

### Redis Caching
```python
# utils/cache.py
class Cache:
    """Redis cache wrapper."""
    
    def __init__(self):
        self.redis = aioredis.from_url(config.redis.url)
    
    async def get(self, key: str) -> Any:
        """Get value from cache."""
        value = await self.redis.get(key)
        return json.loads(value) if value else None
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: int = 300
    ):
        """Set value in cache."""
        await self.redis.setex(
            key,
            expire,
            json.dumps(value)
        )
```

## 🔒 Security

### Authentication
```python
# utils/auth.py
class Auth:
    """Authentication utilities."""
    
    def create_token(self, user_id: str) -> str:
        """Create JWT token."""
        return jwt.encode(
            {
                "sub": user_id,
                "exp": datetime.utcnow() + timedelta(days=1)
            },
            config.api.secret_key,
            algorithm="HS256"
        )
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token."""
        try:
            return jwt.decode(
                token,
                config.api.secret_key,
                algorithms=["HS256"]
            )
        except JWTError:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )
```

### Rate Limiting
```python
# utils/rate_limit.py
class RateLimit:
    """Rate limiting middleware."""
    
    def __init__(self):
        self.redis = aioredis.from_url(config.redis.url)
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int
    ) -> bool:
        """Check if rate limit is exceeded."""
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, window)
        return current <= limit
```

## 📝 Logging

### Logger Configuration
```python
# utils/logger.py
def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=config.log.level,
        format=config.log.format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(config.log.file)
        ]
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
```

### Structured Logging
```python
# utils/logger.py
class StructuredLogger:
    """Structured logging with context."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self.logger.info(
            message,
            extra={
                "timestamp": datetime.utcnow().isoformat(),
                **kwargs
            }
        )
```

## 🧪 Testing

### Unit Tests
```python
# tests/unit/test_supervisor.py
async def test_task_routing():
    """Test supervisor's task routing."""
    supervisor = SupervisorAgent()
    result = await supervisor.handle_task(
        "Create a new pipeline"
    )
    assert result["status"] == "success"
    assert "pipeline" in result
```

### Integration Tests
```python
# tests/integration/test_jenkins.py
async def test_jenkins_integration():
    """Test Jenkins API integration."""
    jenkins = JenkinsAPI()
    job_info = await jenkins.get_job_info("test-job")
    assert job_info["name"] == "test-job"
```

### Mock Testing
```python
# tests/unit/test_agents.py
@pytest.fixture
def mock_jenkins():
    """Mock Jenkins API."""
    with patch("langchain_jenkins.tools.jenkins_api.JenkinsAPI") as mock:
        mock.return_value.get_job_info.return_value = {
            "name": "test-job",
            "url": "http://jenkins/job/test-job"
        }
        yield mock
```

## 🚀 Deployment

### Docker Deployment
```dockerfile
# Dockerfile
FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "langchain_jenkins.web.app:app", "--host", "0.0.0.0"]
```

### Kubernetes Deployment
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jenkins-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: jenkins-agent
  template:
    metadata:
      labels:
        app: jenkins-agent
    spec:
      containers:
      - name: jenkins-agent
        image: jenkins-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: JENKINS_URL
          valueFrom:
            configMapKeyRef:
              name: jenkins-config
              key: jenkins_url
```

## 📈 Monitoring

### Health Checks
```python
# web/routes/health.py
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "dependencies": {
            "jenkins": await check_jenkins(),
            "mongodb": await check_mongodb(),
            "redis": await check_redis()
        }
    }
```

### Metrics Endpoints
```python
# web/routes/metrics.py
@app.get("/metrics/builds")
async def build_metrics():
    """Get build metrics."""
    metrics = await metrics_collector.collect_build_metrics()
    return {
        "total_builds": metrics["total"],
        "success_rate": metrics["success_rate"],
        "avg_duration": metrics["avg_duration"]
    }
```

## 🔧 Development Workflow

1. **Setup Development Environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Code Style**
   ```bash
   # Format code
   black .
   
   # Sort imports
   isort .
   
   # Type checking
   mypy .
   ```

3. **Testing**
   ```bash
   # Run tests
   pytest
   
   # Run with coverage
   pytest --cov=langchain_jenkins
   ```

4. **Local Development**
   ```bash
   # Start development server
   uvicorn langchain_jenkins.web.app:app --reload
   
   # Start dependencies
   docker-compose up redis mongodb
   ```

## 🐛 Debugging

### Debug Configuration
```python
# config/config.py
class DebugConfig(BaseConfig):
    """Debug configuration."""
    
    class Config:
        env_prefix = "DEBUG_"
    
    level: str = "DEBUG"
    log_requests: bool = True
    log_responses: bool = True
```

### Debug Middleware
```python
# web/middleware.py
@app.middleware("http")
async def debug_middleware(request: Request, call_next):
    """Debug middleware for request/response logging."""
    if not config.debug.log_requests:
        return await call_next(request)
    
    logger.debug(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.debug(f"Response: {response.status_code}")
    return response
```

## 📚 Additional Resources

1. [FastAPI Documentation](https://fastapi.tiangolo.com/)
2. [LangChain Documentation](https://python.langchain.com/docs/)
3. [MongoDB Documentation](https://docs.mongodb.com/manual/)
4. [Redis Documentation](https://redis.io/documentation)