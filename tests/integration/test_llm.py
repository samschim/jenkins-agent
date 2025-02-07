"""Integration tests for LLM functionality."""
import json
import pytest
from unittest.mock import AsyncMock
from langchain_jenkins.utils.llm import llm_manager

@pytest.mark.integration
@pytest.mark.asyncio
async def test_lm_studio_generation(monkeypatch):
    """Test text generation using LM Studio."""
    # Mock LM Studio response
    async def mock_generate(prompt, system_prompt=None):
        return {
            "choices": [{
                "message": {
                    "content": "Common causes of Jenkins build failures include:\n1. Missing dependencies\n2. Test failures\n3. Resource constraints"
                }
            }]
        }
    monkeypatch.setattr(llm_manager.lm_studio, "generate", mock_generate)
    
    prompt = "What are the common causes of Jenkins build failures?"
    response = await llm_manager.generate(prompt)
    
    assert isinstance(response, str)
    assert len(response) > 0
    assert "build" in response.lower()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_log_analysis(monkeypatch):
    """Test build log analysis."""
    async def mock_generate(prompt, system_prompt=None):
        return {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "status": "error",
                        "issues": ["Missing dependency", "Build failure"],
                        "recommendations": ["Add dependency", "Check repository"],
                        "severity": "high"
                    })
                }
            }]
        }
    monkeypatch.setattr(llm_manager.lm_studio, "generate", mock_generate)
    
    log = """
    [INFO] Building project...
    [ERROR] Failed to compile: missing dependency org.example:library:1.0.0
    [ERROR] Could not resolve dependencies
    [INFO] BUILD FAILURE
    """
    
    result = await llm_manager.analyze_logs(log)
    
    assert isinstance(result, dict)
    assert "status" in result
    assert "issues" in result
    assert "recommendations" in result
    assert "severity" in result

@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_suggestions(monkeypatch):
    """Test error fix suggestions."""
    async def mock_generate(prompt, system_prompt=None):
        return {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "error_type": "OutOfMemoryError",
                        "causes": ["Insufficient heap space", "Memory leak"],
                        "solutions": ["Increase heap size", "Fix memory leak"],
                        "confidence": 0.9
                    })
                }
            }]
        }
    monkeypatch.setattr(llm_manager.lm_studio, "generate", mock_generate)
    
    error = "java.lang.OutOfMemoryError: Java heap space"
    result = await llm_manager.suggest_fixes(error)
    
    assert isinstance(result, dict)
    assert "error_type" in result
    assert "causes" in result
    assert "solutions" in result
    assert "confidence" in result

@pytest.mark.integration
@pytest.mark.asyncio
async def test_pipeline_optimization(monkeypatch):
    """Test pipeline optimization suggestions."""
    async def mock_generate(prompt, system_prompt=None):
        return {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "issues": ["Redundant Maven commands", "No caching"],
                        "optimizations": ["Use Maven wrapper", "Add caching"],
                        "impact": "high",
                        "risks": ["Build instability"]
                    })
                }
            }]
        }
    monkeypatch.setattr(llm_manager.lm_studio, "generate", mock_generate)
    
    pipeline = """
    pipeline {
        agent any
        stages {
            stage('Build') {
                steps {
                    sh 'mvn clean install'
                }
            }
            stage('Test') {
                steps {
                    sh 'mvn test'
                }
            }
        }
    }
    """
    
    result = await llm_manager.optimize_pipeline(pipeline)
    
    assert isinstance(result, dict)
    assert "issues" in result
    assert "optimizations" in result
    assert "impact" in result
    assert "risks" in result