"""Test pipeline generation and security tools."""
import pytest
from langchain_jenkins.tools.pipeline_generator import PipelineGenerator
from langchain_jenkins.tools.pipeline_security import SecurityScanner

pytestmark = pytest.mark.asyncio

async def test_generate_pipeline(mock_llm):
    """Test pipeline generation."""
    generator = PipelineGenerator()
    
    # Test Java pipeline
    result = await generator.generate_pipeline(
        project_type="java",
        requirements=["Include testing stage", "Include deployment stage"]
    )
    
    assert result["status"] == "success"
    assert "pipeline" in result
    assert "stages" in result["pipeline"]
    assert "test" in result["pipeline"].lower()
    assert "deploy" in result["pipeline"].lower()

async def test_optimize_pipeline(mock_llm):
    """Test pipeline optimization."""
    generator = PipelineGenerator()
    
    # Create a basic pipeline
    pipeline = """pipeline {
        agent any
        stages {
            stage('Build') {
                steps {
                    sh 'mvn clean package'
                }
            }
        }
    }"""
    
    result = await generator.optimize_pipeline(
        pipeline=pipeline,
        project_type="java"
    )
    
    assert result["status"] == "success"
    assert "optimized_pipeline" in result
    assert "improvements" in result
    assert "benefits" in result

async def test_scan_pipeline(mock_llm):
    """Test pipeline security scanning."""
    scanner = SecurityScanner()
    
    # Test pipeline with security issues
    pipeline = """pipeline {
        agent any
        environment {
            PASSWORD = 'secret123'
        }
        stages {
            stage('Build') {
                steps {
                    sh 'mvn clean package'
                }
            }
        }
    }"""
    
    result = await scanner.scan_pipeline(pipeline)
    
    assert result["status"] == "success"
    assert "findings" in result
    assert len(result["findings"]) > 0
    assert result["findings"][0]["severity"] == "high"

async def test_secure_pipeline(mock_llm):
    """Test pipeline security enhancement."""
    scanner = SecurityScanner()
    
    # Test pipeline with security issues
    pipeline = """pipeline {
        agent any
        environment {
            PASSWORD = 'secret123'
        }
        stages {
            stage('Build') {
                steps {
                    sh 'mvn clean package'
                }
            }
        }
    }"""
    
    result = await scanner.secure_pipeline(pipeline)
    
    assert result["status"] == "success"
    assert "secured_pipeline" in result
    assert "improvements" in result
    assert "verification" in result
    assert "PASSWORD = 'secret123'" not in result["secured_pipeline"]

async def test_pipeline_templates(mock_llm):
    """Test pipeline templates."""
    generator = PipelineGenerator()
    
    # Test all project types
    project_types = ["java", "python", "node", "docker"]
    
    for project_type in project_types:
        result = await generator.generate_pipeline(
            project_type=project_type,
            requirements=["Include testing stage"]
        )
        
        assert result["status"] == "success"
        assert project_type in result["pipeline"].lower()
        assert "test" in result["pipeline"].lower()

async def test_security_rules():
    """Test security rules patterns."""
    scanner = SecurityScanner()
    
    # Test each rule
    for rule_name, rule in scanner.rules.items():
        # Create a pipeline with the security issue
        if rule_name == "credentials":
            pipeline = "pipeline { environment { PASSWORD = 'secret' } }"
        elif rule_name == "shell_injection":
            pipeline = "pipeline { steps { sh '${userInput}' } }"
        elif rule_name == "unsafe_git":
            pipeline = "pipeline { steps { sh 'git clone http://example.com' } }"
        else:
            continue
        
        result = await scanner.scan_pipeline(pipeline)
        
        assert result["status"] == "success"
        assert len(result["findings"]) > 0
        assert any(f["rule"] == rule_name for f in result["findings"])

async def test_pipeline_validation(mock_llm):
    """Test pipeline validation."""
    generator = PipelineGenerator()
    
    # Test valid pipeline
    valid_pipeline = """pipeline {
        agent any
        stages {
            stage('Build') {
                steps {
                    sh 'mvn clean package'
                }
            }
        }
    }"""
    
    result = await generator._validate_pipeline(valid_pipeline)
    assert result["valid"] == True
    
    # Test invalid pipeline
    invalid_pipeline = """pipeline {
        agent any
        stages {
            stage('Build') {
                steps {
                    invalid_command
                }
            }
        }
    }"""
    
    result = await generator._validate_pipeline(invalid_pipeline)
    assert result["valid"] == False

async def test_error_handling():
    """Test error handling in pipeline tools."""
    generator = PipelineGenerator()
    scanner = SecurityScanner()
    
    # Test invalid project type
    result = await generator.generate_pipeline(
        project_type="invalid",
        requirements=[]
    )
    assert result["status"] == "error"
    
    # Test invalid pipeline
    result = await scanner.scan_pipeline("invalid pipeline")
    assert result["status"] == "success"  # Should still scan
    assert len(result["findings"]) == 0  # But find no issues