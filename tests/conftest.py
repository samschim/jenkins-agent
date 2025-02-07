"""Test configuration and fixtures."""
import os
import json
import pytest
import asyncio
import platform
import datetime
import pytest_asyncio
import nest_asyncio
import functools
import fakeredis.aioredis
from mongomock_motor import AsyncMongoMockClient
from httpx import AsyncClient
from fastapi.testclient import TestClient
from dotenv import load_dotenv

# Load test environment variables
load_dotenv(".env.test", override=True)

# Enable testing mode
os.environ["TESTING"] = "true"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["MONGODB_URL"] = "mongodb://localhost:27017"
os.environ["MONGODB_DATABASE"] = "jenkins_test"

# Configure asyncio for testing
nest_asyncio.apply()

# Configure event loop for testing
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Configure event loop for testing
if not asyncio._get_running_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

def async_to_sync(func):
    """Convert an async function to sync."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(func(*args, **kwargs))
    return wrapper

def sync_to_async(func):
    """Convert a sync function to async."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)
    return wrapper

from langchain_jenkins.config.config import config
from langchain_jenkins.web.app import app
from langchain_jenkins.db.mongo_client import MongoClient

@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def redis_client():
    """Create Redis client for testing."""
    class MockRedis(fakeredis.aioredis.FakeRedis):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._data = {}

        def zremrangebyscore(self, name, min_score, max_score):
            """Remove all elements in the sorted set with scores between min and max."""
            key = self.exists(name)
            if not key:
                return 0
            removed = 0
            members = self.zrange(name, 0, -1, withscores=True)
            for member, score in members:
                if min_score <= float(score) <= max_score:
                    self.zrem(name, member)
                    removed += 1
            return removed

        async def zremrangebyscore(self, name, min_score, max_score):
            """Remove all elements in the sorted set with scores between min and max."""
            return self.zremrangebyscore(name, min_score, max_score)

        def zadd(self, name, mapping, nx=False, xx=False, ch=False, incr=False):
            """Add elements to a sorted set."""
            if name not in self._data:
                self._data[name] = {}
            for member, score in mapping.items():
                self._data[name][member] = float(score)
            return len(mapping)

        def zrange(self, name, start, end, withscores=False, desc=False):
            """Return a range of elements from a sorted set."""
            if name not in self._data:
                return []
            items = sorted(self._data[name].items(), key=lambda x: x[1], reverse=desc)
            if start < 0:
                start = len(items) + start
            if end < 0:
                end = len(items) + end + 1
            else:
                end += 1
            result = items[start:end]
            if withscores:
                return [(item[0], item[1]) for item in result]
            return [item[0] for item in result]

        def zrem(self, name, *values):
            """Remove elements from a sorted set."""
            if name not in self._data:
                return 0
            removed = 0
            for value in values:
                if value in self._data[name]:
                    del self._data[name][value]
                    removed += 1
            return removed

        def exists(self, name):
            """Check if a key exists."""
            return name in self._data

        def flushdb(self):
            """Clear all data."""
            self._data.clear()
            return True

        async def flushdb(self):
            """Clear all data asynchronously."""
            return self.flushdb()

        def __getattr__(self, name):
            """Handle attribute access."""
            if name == "zremrangebyscore":
                return self.zremrangebyscore
            if name == "zadd":
                return self.zadd
            if name == "zrange":
                return self.zrange
            if name == "zrem":
                return self.zrem
            if name == "exists":
                return self.exists
            if name == "flushdb":
                return self.flushdb
            return super().__getattr__(name)

        def __getattribute__(self, name):
            """Handle attribute access."""
            if name == "zremrangebyscore":
                return object.__getattribute__(self, "zremrangebyscore")
            if name == "zadd":
                return object.__getattribute__(self, "zadd")
            if name == "zrange":
                return object.__getattribute__(self, "zrange")
            if name == "zrem":
                return object.__getattribute__(self, "zrem")
            if name == "exists":
                return object.__getattribute__(self, "exists")
            if name == "flushdb":
                return object.__getattribute__(self, "flushdb")
            return super().__getattribute__(name)

    client = MockRedis()
    yield client
    await client.close()

@pytest_asyncio.fixture(scope="session")
async def mongo_client():
    """Create MongoDB client for testing."""
    class MockMongoClient(AsyncMongoMockClient):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._databases = {}
            self._store = {}
            self._collections = {}
            self.name = config.mongodb.database

        def get_database(self, name=None, codec_options=None, read_preference=None,
                        write_concern=None, read_concern=None):
            if name not in self._databases:
                self._databases[name] = self
            return self._databases[name]

        def __getitem__(self, db_name):
            return self.get_database(db_name)

        def drop_database(self, name_or_database):
            """Drop a database."""
            db_name = name_or_database
            if isinstance(name_or_database, (AsyncMongoMockClient, MongoClient)):
                db_name = name_or_database.name
            if db_name in self._databases:
                del self._databases[db_name]
            if db_name in self._collections:
                del self._collections[db_name]
            return True

        async def drop_database(self, name_or_database):
            """Drop a database asynchronously."""
            return self.drop_database(name_or_database)

        def close(self):
            """Close all databases."""
            self._databases.clear()
            self._store.clear()
            self._collections.clear()

        def get_default_database(self):
            """Get default database."""
            return self[config.mongodb.database]

        def get_collection(self, name):
            """Get a collection."""
            db_name = config.mongodb.database
            if db_name not in self._collections:
                self._collections[db_name] = {}
            if name not in self._collections[db_name]:
                self._collections[db_name][name] = []
            return self._collections[db_name][name]

        def insert_one(self, document):
            """Insert a document synchronously."""
            collection = self.get_collection("default")
            collection.append(document)
            return type("InsertOneResult", (), {
                "inserted_id": document.get("_id"),
                "acknowledged": True
            })

        async def insert_one(self, document):
            """Insert a document asynchronously."""
            return self.insert_one(document)

        def __getattr__(self, name):
            """Handle attribute access."""
            if name == "drop_database":
                return self.drop_database
            if name == "insert_one":
                return self.insert_one
            if name == "get_database":
                return self.get_database
            if name == "get_collection":
                return self.get_collection
            if name == "logs":
                return self.get_default_database()
            if name == "errors":
                return self.get_default_database()
            if name == "trends":
                return self.get_default_database()
            if name == "build_logs":
                return self.get_default_database()
            if name == "build_errors":
                return self.get_default_database()
            if name == "error_trends":
                return self.get_default_database()
            if name == "metrics":
                return self.get_default_database()
            if name == "alerts":
                return self.get_default_database()
            if name == "workflows":
                return self.get_default_database()
            if name == "tasks":
                return self.get_default_database()
            if name == "cache":
                return self.get_default_database()
            return super().__getattr__(name)

        def __getattribute__(self, name):
            """Handle attribute access."""
            if name == "drop_database":
                return object.__getattribute__(self, "drop_database")
            if name == "insert_one":
                return object.__getattribute__(self, "insert_one")
            if name == "get_database":
                return object.__getattribute__(self, "get_database")
            if name == "get_collection":
                return object.__getattribute__(self, "get_collection")
            if name == "logs":
                return object.__getattribute__(self, "get_default_database")()
            if name == "errors":
                return object.__getattribute__(self, "get_default_database")()
            if name == "trends":
                return object.__getattribute__(self, "get_default_database")()
            if name == "build_logs":
                return object.__getattribute__(self, "get_default_database")()
            if name == "build_errors":
                return object.__getattribute__(self, "get_default_database")()
            if name == "error_trends":
                return object.__getattribute__(self, "get_default_database")()
            if name == "metrics":
                return object.__getattribute__(self, "get_default_database")()
            if name == "alerts":
                return object.__getattribute__(self, "get_default_database")()
            if name == "workflows":
                return object.__getattribute__(self, "get_default_database")()
            if name == "tasks":
                return object.__getattribute__(self, "get_default_database")()
            if name == "cache":
                return object.__getattribute__(self, "get_default_database")()
            return super().__getattribute__(name)

    client = MockMongoClient()
    yield client
    client.close()

@pytest.fixture(autouse=True)
async def clean_test_data(redis_client, mongo_client):
    """Clean test data before and after each test."""
    # Clean before test
    await redis_client.flushdb()
    await mongo_client.drop_database(config.mongodb.database)

    yield

    # Clean after test
    await redis_client.flushdb()
    await mongo_client.drop_database(config.mongodb.database)

@pytest.fixture
def mock_jenkins_api(monkeypatch):
    """Mock Jenkins API responses."""
    class MockJenkinsAPI:
        async def get_job_info(self, job_name):
            return {
                "status": "success",
                "job_name": job_name,
                "info": {
                    "name": job_name,
                    "url": f"http://jenkins/{job_name}",
                    "buildable": True,
                    "lastBuild": {
                        "number": 1,
                        "duration": 1000,
                        "timestamp": 1644825600000
                    }
                }
            }

        async def build_job(self, job_name, parameters=None):
            return {
                "status": "success",
                "job_name": job_name,
                "build_number": 123,
                "queue_id": 456
            }

        async def get_build_log(self, job_name, build_number):
            return {
                "status": "success",
                "job_name": job_name,
                "build_number": build_number,
                "log": "[INFO] Build successful"
            }

        async def get_plugins(self):
            return {
                "status": "success",
                "plugins": [
                    {"name": "git", "version": "1.0.0"},
                    {"name": "pipeline", "version": "2.0.0"}
                ]
            }

        async def get_system_info(self):
            return {
                "status": "success",
                "info": {
                    "version": "2.0.0",
                    "nodes": 1,
                    "memory": "2GB"
                }
            }

        async def create_job(self, job_name, config_xml=None):
            return {
                "status": "success",
                "message": f"Created job {job_name}",
                "url": f"http://jenkins/job/{job_name}"
            }

    monkeypatch.setattr(
        "langchain_jenkins.tools.jenkins_api.JenkinsAPI",
        lambda: MockJenkinsAPI()
    )
    return MockJenkinsAPI()

@pytest.fixture
def mock_llm(monkeypatch):
    """Mock LLM responses."""
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.messages import BaseMessage, AIMessage, SystemMessage
    from langchain_core.outputs import ChatResult, ChatGeneration
    from langchain_core.runnables import RunnableConfig, Runnable
    from langchain_core.callbacks.manager import CallbackManagerForLLMRun
    from typing import List, Any, Optional, Dict, Union, Sequence, TypeVar, cast

    Input = TypeVar("Input")
    Output = TypeVar("Output")

    class MockLLM(BaseChatModel):
        @property
        def _llm_type(self) -> str:
            return "mock"

        @property
        def _identifying_params(self) -> Dict[str, Any]:
            return {"model": "mock"}

        def _combine_llm_outputs(self, llm_outputs: List[Optional[dict]]) -> dict:
            return {"model": "mock"}

        def _generate(
            self,
            messages: List[BaseMessage],
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
        ) -> ChatResult:
            prompt = messages[-1].content.lower()
            system_prompt = next(
                (m.content for m in messages if isinstance(m, SystemMessage)),
                None
            )

            if system_prompt and "json" in system_prompt.lower():
                if "analyze" in prompt:
                    content = {
                        "status": "success",
                        "issues": ["test issue"],
                        "recommendations": ["test recommendation"],
                        "severity": "medium",
                        "result": "success",
                        "message": "Mocked JSON response",
                        "valid": True,
                        "job": "test-job",
                        "build": 123,
                        "duration": 300,
                        "error": None,
                        "agent_type": "log",
                        "task": "Analyze",
                        "plugin": "test-plugin",
                        "pipeline": {
                            "status": "success",
                            "task": "Install git plugin and create a pipeline job",
                            "error": None
                        }
                    }
                elif "error" in prompt:
                    content = {
                        "error_type": "test_error",
                        "causes": ["test cause"],
                        "solutions": ["test solution"],
                        "confidence": 0.8,
                        "result": "success",
                        "message": "Mocked JSON response",
                        "valid": True,
                        "job": "test-job",
                        "build": 123,
                        "duration": 300,
                        "error": None,
                        "agent_type": "log",
                        "task": "Analyze",
                        "plugin": "test-plugin",
                        "pipeline": {
                            "status": "success",
                            "task": "Install git plugin and create a pipeline job",
                            "error": None
                        }
                    }
                elif "pipeline" in prompt:
                    content = {
                        "issues": ["test issue"],
                        "optimizations": ["test optimization"],
                        "impact": "medium",
                        "risks": ["test risk"],
                        "result": "success",
                        "message": "Mocked JSON response",
                        "valid": True,
                        "job": "test-job",
                        "build": 123,
                        "duration": 300,
                        "error": None,
                        "agent_type": "log",
                        "task": "Analyze",
                        "plugin": "test-plugin",
                        "pipeline": {
                            "status": "success",
                            "task": "Install git plugin and create a pipeline job",
                            "error": None
                        }
                    }
                else:
                    content = {
                        "result": "success",
                        "message": "Mocked JSON response",
                        "valid": True,
                        "job": "test-job",
                        "build": 123,
                        "duration": 300,
                        "error": None,
                        "agent_type": "log",
                        "task": "Analyze",
                        "plugin": "test-plugin",
                        "pipeline": {
                            "status": "success",
                            "task": "Install git plugin and create a pipeline job",
                            "error": None
                        }
                    }
                content = json.dumps(content, ensure_ascii=False, default=str)
            else:
                content = json.dumps({
                    "result": "success",
                    "message": "Mocked LLM response",
                    "valid": True,
                    "job": "test-job",
                    "build": 123,
                    "duration": 300,
                    "error": None,
                    "agent_type": "log",
                    "task": "Analyze",
                    "plugin": "test-plugin",
                    "pipeline": {
                        "status": "success",
                        "task": "Install git plugin and create a pipeline job",
                        "error": None
                    }
                }, ensure_ascii=False, default=str)

            return ChatResult(generations=[
                ChatGeneration(message=AIMessage(content=content))
            ])

        async def _agenerate(
            self,
            messages: List[BaseMessage],
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
        ) -> ChatResult:
            return self._generate(messages, stop, run_manager, **kwargs)

    monkeypatch.setattr(
        "langchain_jenkins.utils.llm.ChatOpenAI",
        lambda **kwargs: MockLLM()
    )
    monkeypatch.setattr(
        "langchain_jenkins.agents.base_agent.ChatOpenAI",
        lambda **kwargs: MockLLM()
    )
    return MockLLM()

@pytest.fixture
def mock_webhook(monkeypatch):
    """Mock webhook notifications."""
    class MockWebhook:
        def __init__(self):
            self.events = []

        async def send(self, payload):
            self.events.append(payload)
            return {"status": "success"}

        async def verify(self):
            return True

        async def notify(self, event_type, data):
            payload = {
                "event": event_type,
                "data": data,
                "timestamp": str(datetime.datetime.now(datetime.UTC))
            }
            return await self.send(payload)

        async def send_notification(self, message: str, **kwargs):
            return await self.notify("notification", {
                "message": message,
                **kwargs
            })

        async def send_alert(self, alert_type: str, message: str, **kwargs):
            return await self.notify("alert", {
                "alert_type": alert_type,
                "message": message,
                **kwargs
            })

    monkeypatch.setattr(
        "langchain_jenkins.utils.webhook.WebhookHandler",
        lambda **kwargs: MockWebhook()
    )
    monkeypatch.setattr(
        "langchain_jenkins.utils.webhook.WebhookNotifier",
        lambda: MockWebhook()
    )
    monkeypatch.setattr(
        "langchain_jenkins.webhooks.notifier.NotificationService",
        lambda: MockWebhook()
    )
    return MockWebhook()

@pytest.fixture
def mock_prometheus(monkeypatch):
    """Mock Prometheus metrics."""
    class MockPrometheus:
        def __init__(self):
            self.values = {}
            self.counters = {}
            self.gauges = {}
            self.histograms = {}

        def inc(self, amount=1, labels=None):
            key = str(labels) if labels else "default"
            self.values[key] = self.values.get(key, 0) + amount

        def dec(self, amount=1, labels=None):
            key = str(labels) if labels else "default"
            self.values[key] = self.values.get(key, 0) - amount

        def set(self, value, labels=None):
            key = str(labels) if labels else "default"
            self.values[key] = value

        def get(self, labels=None):
            key = str(labels) if labels else "default"
            return self.values.get(key, 0)

        def observe(self, value, labels=None):
            key = str(labels) if labels else "default"
            if key not in self.histograms:
                self.histograms[key] = []
            self.histograms[key].append(value)

        def clear(self):
            self.values.clear()
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()

    mock = MockPrometheus()
    monkeypatch.setattr(
        "langchain_jenkins.utils.monitoring.Counter",
        lambda *args, **kwargs: mock
    )
    monkeypatch.setattr(
        "langchain_jenkins.utils.monitoring.Gauge",
        lambda *args, **kwargs: mock
    )
    monkeypatch.setattr(
        "langchain_jenkins.utils.monitoring.Histogram",
        lambda *args, **kwargs: mock
    )
    monkeypatch.setattr(
        "prometheus_client.Counter",
        lambda *args, **kwargs: mock
    )
    monkeypatch.setattr(
        "prometheus_client.Gauge",
        lambda *args, **kwargs: mock
    )
    monkeypatch.setattr(
        "prometheus_client.Histogram",
        lambda *args, **kwargs: mock
    )
    return mock