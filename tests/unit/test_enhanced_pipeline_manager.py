"""Unit tests for enhanced pipeline manager agent."""
import pytest
from unittest.mock import AsyncMock, patch
from langchain_jenkins.agents.enhanced_pipeline_manager import (
    EnhancedPipelineManager,
    PipelineStage,
    PipelineConfig
)

@pytest.fixture
def pipeline_manager():
    """Create a pipeline manager for testing."""
    manager = EnhancedPipelineManager()
    manager.jenkins = AsyncMock()
    manager.llm = AsyncMock()
    return manager

@pytest.fixture
def sample_pipeline():
    """Create a sample pipeline configuration."""
    return PipelineConfig(
        name="test-pipeline",
        stages=[
            PipelineStage(
                name="Build",
                steps=[{"type": "sh", "command": "mvn clean install"}],
                conditions=["branch 'main'"],
                environment={"JAVA_HOME": "/usr/lib/jvm/java-11"},
                agents=["maven"]
            ),
            PipelineStage(
                name="Test",
                steps=[{"type": "sh", "command": "mvn test"}],
                conditions=["branch 'main'"],
                environment={"TEST_ENV": "true"},
                agents=["maven"]
            )
        ],
        triggers=["pollSCM('H/15 * * * *')"],
        environment={"GLOBAL_VAR": "value"},
        parameters=[{"name": "BRANCH", "type": "string", "default": "main"}],
        post_actions={
            "success": ["emailext subject: 'Success'"],
            "failure": ["emailext subject: 'Failed'"]
        }
    )

@pytest.fixture
def sample_jenkinsfile():
    """Create a sample Jenkinsfile."""
    return """
pipeline {
    agent any
    environment {
        GLOBAL_VAR = 'value'
    }
    parameters {
        string(name: 'BRANCH', defaultValue: 'main', description: '')
    }
    triggers {
        pollSCM('H/15 * * * *')
    }
    stages {
        stage('Build') {
            agent { label 'maven' }
            when { branch 'main' }
            environment {
                JAVA_HOME = '/usr/lib/jvm/java-11'
            }
            steps {
                sh 'mvn clean install'
            }
        }
        stage('Test') {
            agent { label 'maven' }
            when { branch 'main' }
            environment {
                TEST_ENV = 'true'
            }
            steps {
                sh 'mvn test'
            }
        }
    }
    post {
        success {
            emailext subject: 'Success'
        }
        failure {
            emailext subject: 'Failed'
        }
    }
}
"""

@pytest.mark.asyncio
async def test_get_pipeline(pipeline_manager, sample_pipeline):
    """Test getting pipeline configuration."""
    pipeline_manager.jenkins.get.return_value = f"""<?xml version="1.0" encoding="UTF-8"?>
<flow-definition>
    <actions/>
    <description>test-pipeline Pipeline</description>
    <keepDependencies>false</keepDependencies>
    <properties>
        <parameters>{[{"name": "BRANCH", "type": "string", "default": "main"}]}</parameters>
    </properties>
    <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition">
        <script>
            pipeline {{
                agent any
                environment {{"GLOBAL_VAR": "value"}}
                triggers {["pollSCM('H/15 * * * *')"]}
                stages {{
                    stage('Build') {{
                        agent {{ label 'maven' }}
                        when {{ branch 'main' }}
                        environment {{"JAVA_HOME": "/usr/lib/jvm/java-11"}}
                        steps {{
                            sh 'mvn clean install'
                        }}
                    }}
                    stage('Test') {{
                        agent {{ label 'maven' }}
                        when {{ branch 'main' }}
                        environment {{"TEST_ENV": "true"}}
                        steps {{
                            sh 'mvn test'
                        }}
                    }}
                }}
                post {{
                    success {{
                        emailext subject: 'Success'
                    }}
                    failure {{
                        emailext subject: 'Failed'
                    }}
                }}
            }}
        </script>
    </definition>
</flow-definition>"""
    
    result = await pipeline_manager._get_pipeline("test-pipeline")
    
    assert isinstance(result, PipelineConfig)
    assert result.name == "test-pipeline"
    assert len(result.stages) == 2
    assert result.stages[0].name == "Build"
    assert result.stages[1].name == "Test"

@pytest.mark.asyncio
async def test_update_pipeline(pipeline_manager, sample_pipeline):
    """Test updating pipeline configuration."""
    pipeline_manager._validate_pipeline = AsyncMock(return_value={
        "valid": True,
        "issues": [],
        "suggestions": [],
        "security_concerns": [],
        "best_practices": []
    })
    
    result = await pipeline_manager._update_pipeline(sample_pipeline)
    
    assert result["status"] == "updated"
    assert result["pipeline"] == "test-pipeline"

@pytest.mark.asyncio
async def test_validate_pipeline(pipeline_manager, sample_pipeline):
    """Test pipeline validation."""
    pipeline_manager.llm.agenerate.return_value.generations[0].text = """{
        "valid": true,
        "issues": [],
        "suggestions": ["Add more tests"],
        "security_concerns": [],
        "best_practices": ["Use version tags"]
    }"""
    
    result = await pipeline_manager._validate_pipeline(sample_pipeline)
    
    assert result["valid"] is True
    assert len(result["suggestions"]) == 1
    assert len(result["best_practices"]) == 1

@pytest.mark.asyncio
async def test_get_jenkinsfile(pipeline_manager, sample_jenkinsfile):
    """Test getting Jenkinsfile content."""
    pipeline_manager.jenkins.get.return_value = """
<flow-definition>
    <remote>https://github.com/test/repo</remote>
</flow-definition>
"""
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": "base64_encoded_content"
        }
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )
        
        result = await pipeline_manager._get_jenkinsfile("test-pipeline")
        
        assert isinstance(result, str)
        assert "base64_encoded_content" in str(result)

@pytest.mark.asyncio
async def test_update_jenkinsfile(pipeline_manager, sample_jenkinsfile):
    """Test updating Jenkinsfile content."""
    pipeline_manager.jenkins.get.return_value = """
<flow-definition>
    <remote>https://github.com/test/repo</remote>
</flow-definition>
"""
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock()
        mock_get.status_code = 200
        mock_get.json.return_value = {
            "sha": "old_sha"
        }
        
        mock_put = AsyncMock()
        mock_put.status_code = 200
        mock_put.json.return_value = {
            "commit": {"sha": "new_sha"}
        }
        
        mock_client.return_value.__aenter__.return_value.get = mock_get
        mock_client.return_value.__aenter__.return_value.put = mock_put
        
        result = await pipeline_manager._update_jenkinsfile(
            "test-pipeline",
            sample_jenkinsfile
        )
        
        assert result["status"] == "updated"
        assert result["commit"] == "new_sha"

@pytest.mark.asyncio
async def test_manage_dependencies(pipeline_manager, sample_pipeline):
    """Test managing pipeline dependencies."""
    pipeline_manager._get_pipeline = AsyncMock(return_value=sample_pipeline)
    pipeline_manager._update_pipeline = AsyncMock(return_value={
        "status": "updated",
        "pipeline": "test-pipeline"
    })
    
    result = await pipeline_manager._manage_dependencies(
        "test-pipeline",
        upstream=["job1", "job2"],
        downstream=["job3", "job4"]
    )
    
    assert result["status"] == "updated"
    assert result["pipeline"] == "test-pipeline"

@pytest.mark.asyncio
async def test_sync_with_git(pipeline_manager, sample_jenkinsfile):
    """Test syncing pipeline with Git."""
    pipeline_manager._get_jenkinsfile = AsyncMock(
        return_value=sample_jenkinsfile
    )
    pipeline_manager._parse_jenkinsfile = AsyncMock(
        return_value=sample_pipeline
    )
    pipeline_manager._update_pipeline = AsyncMock(return_value={
        "status": "updated",
        "pipeline": "test-pipeline"
    })
    
    result = await pipeline_manager._sync_with_git("test-pipeline")
    
    assert result["status"] == "updated"
    assert result["pipeline"] == "test-pipeline"

@pytest.mark.asyncio
async def test_handle_task_get_pipeline(pipeline_manager, sample_pipeline):
    """Test handling get pipeline task."""
    pipeline_manager._get_pipeline = AsyncMock(return_value=sample_pipeline)
    
    result = await pipeline_manager.handle_task(
        "get pipeline test-pipeline"
    )
    
    assert result["status"] == "success"
    assert result["pipeline"]["name"] == "test-pipeline"

@pytest.mark.asyncio
async def test_handle_task_update_pipeline(pipeline_manager, sample_pipeline):
    """Test handling update pipeline task."""
    pipeline_manager._update_pipeline = AsyncMock(return_value={
        "status": "updated",
        "pipeline": "test-pipeline"
    })
    
    result = await pipeline_manager.handle_task(
        f"update pipeline config {vars(sample_pipeline)}"
    )
    
    assert result["status"] == "updated"
    assert result["pipeline"] == "test-pipeline"

@pytest.mark.asyncio
async def test_handle_task_validate_pipeline(pipeline_manager, sample_pipeline):
    """Test handling validate pipeline task."""
    pipeline_manager._validate_pipeline = AsyncMock(return_value={
        "valid": True,
        "issues": [],
        "suggestions": [],
        "security_concerns": [],
        "best_practices": []
    })
    
    result = await pipeline_manager.handle_task(
        f"validate pipeline config {vars(sample_pipeline)}"
    )
    
    assert result["valid"] is True

@pytest.mark.asyncio
async def test_handle_task_jenkinsfile(pipeline_manager, sample_jenkinsfile):
    """Test handling Jenkinsfile task."""
    pipeline_manager._get_jenkinsfile = AsyncMock(
        return_value=sample_jenkinsfile
    )
    
    result = await pipeline_manager.handle_task(
        "get jenkinsfile test-pipeline"
    )
    
    assert result["status"] == "success"
    assert "pipeline" in result["jenkinsfile"]

@pytest.mark.asyncio
async def test_handle_task_dependencies(pipeline_manager):
    """Test handling dependencies task."""
    pipeline_manager._manage_dependencies = AsyncMock(return_value={
        "status": "updated",
        "pipeline": "test-pipeline"
    })
    
    result = await pipeline_manager.handle_task(
        "set dependencies for test-pipeline upstream job1 job2 downstream job3 job4"
    )
    
    assert result["status"] == "updated"
    assert result["pipeline"] == "test-pipeline"

@pytest.mark.asyncio
async def test_handle_task_git_sync(pipeline_manager):
    """Test handling Git sync task."""
    pipeline_manager._sync_with_git = AsyncMock(return_value={
        "status": "updated",
        "pipeline": "test-pipeline"
    })
    
    result = await pipeline_manager.handle_task(
        "sync pipeline test-pipeline with git branch main"
    )
    
    assert result["status"] == "updated"
    assert result["pipeline"] == "test-pipeline"