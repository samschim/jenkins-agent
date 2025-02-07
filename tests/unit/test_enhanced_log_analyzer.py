"""Unit tests for enhanced log analyzer agent."""
import pytest
from unittest.mock import AsyncMock, patch
from langchain_jenkins.agents.enhanced_log_analyzer import (
    EnhancedLogAnalyzer,
    ErrorPattern,
    LogAnalysis
)

@pytest.fixture
def log_analyzer():
    """Create a log analyzer for testing."""
    analyzer = EnhancedLogAnalyzer()
    analyzer.llm = AsyncMock()
    return analyzer

@pytest.fixture
def sample_log():
    """Create a sample build log."""
    return """
[INFO] Building project
[ERROR] java.lang.OutOfMemoryError: Java heap space
    at java.base/java.util.Arrays.copyOf(Arrays.java:3745)
    at java.base/java.lang.AbstractStringBuilder.ensureCapacityInternal(AbstractStringBuilder.java:172)
[ERROR] Connection refused: connect
    at java.base/java.net.PlainSocketImpl.connect0(Native Method)
    at java.base/java.net.PlainSocketImpl.socketConnect(PlainSocketImpl.java:101)
[ERROR] Permission denied: /var/lib/jenkins/workspace/test
    at java.base/java.io.UnixFileSystem.createFileExclusively(Native Method)
    at java.base/java.io.File.createNewFile(File.java:1043)
"""

@pytest.fixture
def sample_analysis():
    """Create a sample log analysis."""
    return LogAnalysis(
        patterns=[
            ErrorPattern(
                pattern="OutOfMemoryError",
                frequency=1,
                severity="high",
                context="JVM heap space",
                examples=["java.lang.OutOfMemoryError: Java heap space"],
                solutions=["Increase heap size"]
            )
        ],
        error_types=["Memory Error"],
        root_causes=["Insufficient heap space"],
        recommendations=["Increase heap size"],
        severity="high",
        summary="Build failed due to memory issues"
    )

@pytest.mark.asyncio
async def test_analyze_log(log_analyzer, sample_log):
    """Test log analysis."""
    log_analyzer.llm.agenerate.return_value.generations[0].text = """{
        "patterns": [],
        "error_types": ["Memory Error", "Network Error", "Permission Error"],
        "root_causes": ["Insufficient resources"],
        "recommendations": ["Increase resources"],
        "severity": "high",
        "summary": "Multiple errors detected"
    }"""
    
    result = await log_analyzer._analyze_log(sample_log)
    
    assert isinstance(result, LogAnalysis)
    assert len(result.patterns) == 3  # Three known patterns
    assert "Memory Error" in result.error_types
    assert result.severity == "high"

@pytest.mark.asyncio
async def test_create_ticket_jira(log_analyzer, sample_analysis):
    """Test Jira ticket creation."""
    result = await log_analyzer._create_ticket(sample_analysis, "jira")
    
    assert result["status"] == "created"
    assert result["system"] == "jira"
    assert "Memory Error" in result["ticket"]["title"]
    assert "high" == result["ticket"]["severity"]

@pytest.mark.asyncio
async def test_create_ticket_github(log_analyzer, sample_analysis):
    """Test GitHub issue creation."""
    result = await log_analyzer._create_ticket(sample_analysis, "github")
    
    assert result["status"] == "created"
    assert result["system"] == "github"
    assert "Memory Error" in result["ticket"]["title"]
    assert "high" == result["ticket"]["severity"]

@pytest.mark.asyncio
async def test_get_solutions_known_pattern(log_analyzer):
    """Test getting solutions for known pattern."""
    result = await log_analyzer._get_solutions("OutOfMemoryError")
    
    assert len(result) == 3
    assert "Increase heap size" in result[0]

@pytest.mark.asyncio
async def test_get_solutions_unknown_pattern(log_analyzer):
    """Test getting solutions for unknown pattern."""
    log_analyzer.llm.agenerate.return_value.generations[0].text = """[
        "Check system resources",
        "Verify configuration"
    ]"""
    
    result = await log_analyzer._get_solutions("Unknown error")
    
    assert len(result) == 2
    assert "Check system resources" in result

@pytest.mark.asyncio
async def test_update_knowledge_base_new_pattern(log_analyzer):
    """Test adding new pattern to knowledge base."""
    result = await log_analyzer._update_knowledge_base(
        "NewError",
        ["Solution 1", "Solution 2"],
        "high",
        "New error context"
    )
    
    assert result["status"] == "added"
    assert result["pattern"] == "NewError"

@pytest.mark.asyncio
async def test_update_knowledge_base_existing_pattern(log_analyzer):
    """Test updating existing pattern."""
    # Add pattern first
    await log_analyzer._update_knowledge_base(
        "OutOfMemoryError",
        ["New solution"],
        "medium",
        "Updated context"
    )
    
    result = await log_analyzer._update_knowledge_base(
        "OutOfMemoryError",
        ["Updated solution"],
        "high",
        "New context"
    )
    
    assert result["status"] == "updated"
    assert result["pattern"] == "OutOfMemoryError"

@pytest.mark.asyncio
async def test_handle_task_analysis(log_analyzer, sample_log):
    """Test handling analysis task."""
    log_analyzer._analyze_log = AsyncMock(return_value=LogAnalysis(
        patterns=[],
        error_types=["Test Error"],
        root_causes=["Test Cause"],
        recommendations=["Test Fix"],
        severity="medium",
        summary="Test summary"
    ))
    
    result = await log_analyzer.handle_task(f"analyze {sample_log}")
    
    assert result["status"] == "success"
    assert "Test Error" in result["analysis"]["error_types"]
    assert result["analysis"]["severity"] == "medium"

@pytest.mark.asyncio
async def test_handle_task_ticket(log_analyzer, sample_analysis):
    """Test handling ticket creation task."""
    log_analyzer._create_ticket = AsyncMock(return_value={
        "status": "created",
        "system": "jira",
        "ticket": {"id": "TEST-1"}
    })
    
    result = await log_analyzer.handle_task(
        f"create ticket for analysis {sample_analysis}"
    )
    
    assert result["status"] == "created"
    assert result["system"] == "jira"
    assert "ticket" in result

@pytest.mark.asyncio
async def test_handle_task_solution(log_analyzer):
    """Test handling solution request task."""
    log_analyzer._get_solutions = AsyncMock(return_value=[
        "Test solution"
    ])
    
    result = await log_analyzer.handle_task(
        "get solution for TestError"
    )
    
    assert result["status"] == "success"
    assert "Test solution" in result["solutions"]

@pytest.mark.asyncio
async def test_handle_task_pattern(log_analyzer):
    """Test handling pattern update task."""
    result = await log_analyzer.handle_task(
        "add pattern TestError solutions: Fix 1, Fix 2 severity: high context: Test context"
    )
    
    assert result["status"] == "added"
    assert result["pattern"] == "TestError"