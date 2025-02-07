"""Configuration module for LangChain Jenkins Agent."""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class JenkinsConfig:
    """Jenkins configuration settings."""
    url: str = os.getenv("JENKINS_URL", "http://localhost:8080")
    user: str = os.getenv("JENKINS_USER", "admin")
    api_token: str = os.getenv("JENKINS_API_TOKEN", "")
    verify_ssl: bool = os.getenv("JENKINS_VERIFY_SSL", "true").lower() == "true"

@dataclass
class LLMConfig:
    """LLM configuration settings."""
    model: str = os.getenv("LLM_MODEL", "gpt-4")
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0"))
    api_key: str = os.getenv("OPENAI_API_KEY", "")

@dataclass
class Config:
    """Global configuration settings."""
    jenkins: JenkinsConfig = JenkinsConfig()
    llm: LLMConfig = LLMConfig()
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

# Global config instance
config = Config()