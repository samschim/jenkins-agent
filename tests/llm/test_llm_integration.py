"""LLM integration tests."""
import json
import pytest
from langchain_jenkins.utils.llm import llm_manager

pytestmark = [pytest.mark.llm, pytest.mark.asyncio]

async def test_text_generation(mock_llm):
    """Test basic text generation."""
    prompt = "What are the common causes of Jenkins build failures?"
    response = await llm_manager.generate(prompt)
    
    assert isinstance(response, str)
    assert len(response) > 0

async def test_json_response(mock_llm):
    """Test generating JSON-formatted responses."""
    prompt = "Analyze this build log"
    system_prompt = """You are a Jenkins expert.
Format your response as JSON with these keys:
- status: success/failure
- issues: list of issues found
- recommendations: list of fixes"""
    
    response = await llm_manager.generate(prompt, system_prompt)
    data = json.loads(response)
    
    assert isinstance(data, dict)
    assert "status" in data
    assert "issues" in data
    assert "recommendations" in data
    assert isinstance(data["issues"], list)
    assert len(data["issues"]) > 0

async def test_error_analysis(mock_llm):
    """Test analyzing build errors."""
    error = "java.lang.OutOfMemoryError: Java heap space"
    system_prompt = """You are a Jenkins expert.
Analyze this error and provide solutions."""
    
    response = await llm_manager.generate(error, system_prompt)
    data = json.loads(response)
    
    assert isinstance(data, dict)
    assert "error_type" in data
    assert "causes" in data
    assert "solutions" in data
    assert "confidence" in data
    assert len(data["solutions"]) > 0

async def test_pipeline_optimization(mock_llm):
    """Test pipeline optimization suggestions."""
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
    system_prompt = """You are a Jenkins expert.
Analyze this pipeline and suggest optimizations."""
    
    response = await llm_manager.generate(pipeline, system_prompt)
    data = json.loads(response)
    
    assert isinstance(data, dict)
    assert "issues" in data
    assert "optimizations" in data
    assert "impact" in data
    assert "risks" in data
    assert isinstance(data["optimizations"], list)
    assert len(data["optimizations"]) > 0

async def test_log_analysis(mock_llm):
    """Test build log analysis."""
    log = """
    [INFO] Building project...
    [ERROR] Failed to compile: missing dependency org.example:library:1.0.0
    [ERROR] Could not resolve dependencies
    [INFO] BUILD FAILURE
    """
    system_prompt = """You are a Jenkins expert.
Analyze this build log and identify issues."""
    
    response = await llm_manager.generate(log, system_prompt)
    data = json.loads(response)
    
    assert isinstance(data, dict)
    assert "status" in data
    assert "issues" in data
    assert "recommendations" in data
    assert "severity" in data
    assert len(data["issues"]) > 0

async def test_error_handling(mock_llm):
    """Test error handling in LLM responses."""
    # Test with error prompt
    prompt = "Handle this error"
    response = await llm_manager.generate(prompt)
    data = json.loads(response)
    
    assert isinstance(data, dict)
    assert "error_type" in data
    assert "causes" in data
    assert "solutions" in data
    assert "confidence" in data