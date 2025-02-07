"""Unit tests for AI log analyzer."""
import pytest
from unittest.mock import AsyncMock, patch
from langchain_jenkins.ai.log_analyzer import (
    AILogAnalyzer,
    BuildTroubleshooter,
    LogPattern,
    LogAnalysis
)

@pytest.fixture
def log_analyzer():
    """Create a log analyzer for testing."""
    analyzer = AILogAnalyzer()
    analyzer.analysis_chain = AsyncMock()
    analyzer.prediction_chain = AsyncMock()
    return analyzer

@pytest.fixture
def troubleshooter():
    """Create a build troubleshooter for testing."""
    troubleshooter = BuildTroubleshooter()
    troubleshooter.troubleshoot_chain = AsyncMock()
    return troubleshooter

@pytest.mark.asyncio
async def test_analyze_log(log_analyzer):
    """Test log analysis."""
    # Mock AI response
    log_analyzer.analysis_chain.arun.return_value = """{
        "patterns": [
            {
                "pattern": "OutOfMemoryError",
                "frequency": 2,
                "severity": "high",
                "context": "Java heap space"
            }
        ],
        "error_types": ["Memory Error"],
        "root_causes": ["Insufficient heap space"],
        "recommendations": ["Increase heap size"],
        "severity": "high"
    }"""
    
    result = await log_analyzer.analyze_log("test log")
    
    assert isinstance(result, LogAnalysis)
    assert len(result.patterns) == 1
    assert result.patterns[0].pattern == "OutOfMemoryError"
    assert result.severity == "high"

@pytest.mark.asyncio
async def test_predict_failures(log_analyzer):
    """Test failure prediction."""
    # Mock AI response
    log_analyzer.prediction_chain.arun.return_value = """{
        "failure_probability": 0.8,
        "risk_factors": ["Memory usage"],
        "warning_signs": ["High heap usage"],
        "preventive_actions": ["Increase memory"]
    }"""
    
    build_history = [
        {"result": "SUCCESS"},
        {"result": "FAILURE"}
    ]
    
    result = await log_analyzer.predict_failures(build_history)
    
    assert isinstance(result, dict)
    assert result["failure_probability"] == 0.8
    assert "risk_factors" in result

def test_extract_log_sections(log_analyzer):
    """Test log section extraction."""
    log_text = """
    ERROR: Build failed
    Details: Test failed
    
    [Step 1] Running step: compile
    Output: Success
    
    Test MyTest FAILED
    Details: Assertion failed
    """
    
    sections = log_analyzer._extract_log_sections(log_text)
    
    assert len(sections) == 3  # Error, step, and test sections
    assert any("ERROR" in s for s in sections)
    assert any("Running step" in s for s in sections)
    assert any("FAILED" in s for s in sections)

@pytest.mark.asyncio
async def test_troubleshoot_failure(troubleshooter):
    """Test build troubleshooting."""
    # Mock AI response
    troubleshooter.troubleshoot_chain.arun.return_value = """{
        "diagnosis": "Memory issue",
        "steps": ["Check heap size"],
        "verification": ["Monitor memory"],
        "prevention": ["Increase limits"]
    }"""
    
    build_info = {"result": "FAILURE"}
    log_analysis = LogAnalysis(
        patterns=[
            LogPattern(
                pattern="OutOfMemoryError",
                frequency=1,
                severity="high",
                context="heap space"
            )
        ],
        error_types=["Memory Error"],
        root_causes=["Insufficient memory"],
        recommendations=["Increase memory"],
        severity="high"
    )
    
    result = await troubleshooter.troubleshoot_failure(
        build_info,
        log_analysis
    )
    
    assert isinstance(result, dict)
    assert "diagnosis" in result
    assert "steps" in result
    assert "verification" in result
    assert "prevention" in result