"""Enhanced Log Analysis Agent with advanced features.

Features:
- Pattern recognition
- Error classification
- Solution recommendations
- Automated ticket creation
- Integration with issue tracking
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import re
import json
import httpx
from langchain.tools import Tool
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from .base_agent import BaseAgent
from ..config.config import config
from ..utils.cache import cache
from ..utils.error_handler import handle_errors

@dataclass
class ErrorPattern:
    """Error pattern information."""
    pattern: str
    frequency: int
    severity: str
    context: str
    examples: List[str]
    solutions: List[str]

@dataclass
class LogAnalysis:
    """Log analysis results."""
    patterns: List[ErrorPattern]
    error_types: List[str]
    root_causes: List[str]
    recommendations: List[str]
    severity: str
    summary: str

class EnhancedLogAnalyzer(BaseAgent):
    """Enhanced agent for analyzing build logs."""
    
    def __init__(self):
        """Initialize log analyzer with enhanced capabilities."""
        self.llm = ChatOpenAI(
            model=config.llm.model,
            temperature=0.1
        )
        
        # Create analysis chain
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at analyzing Jenkins build logs.
Analyze the log for patterns, errors, and provide solutions.

Format your response as JSON with these keys:
- patterns: list of error patterns with frequency, severity, context
- error_types: list of identified error types
- root_causes: list of potential root causes
- recommendations: list of specific solutions
- severity: overall severity (low, medium, high)
- summary: brief analysis summary"""),
            ("human", "{log_text}")
        ])
        
        tools = [
            Tool(
                name="AnalyzeLog",
                func=self._analyze_log,
                description="Analyze a build log for patterns and errors"
            ),
            Tool(
                name="CreateTicket",
                func=self._create_ticket,
                description="Create a ticket for a build issue"
            ),
            Tool(
                name="GetSolutions",
                func=self._get_solutions,
                description="Get solution recommendations for an error"
            ),
            Tool(
                name="UpdateKnowledgeBase",
                func=self._update_knowledge_base,
                description="Update the error pattern knowledge base"
            )
        ]
        
        super().__init__(tools)
    
    @handle_errors()
    async def _analyze_log(
        self,
        log_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> LogAnalysis:
        """Analyze a build log.
        
        Args:
            log_text: Build log content
            context: Optional analysis context
            
        Returns:
            Log analysis results
        """
        # Get cached patterns
        known_patterns = await self._get_known_patterns()
        
        # Find known patterns
        patterns = []
        for pattern in known_patterns:
            matches = re.finditer(pattern["pattern"], log_text)
            examples = [m.group(0) for m in matches]
            if examples:
                patterns.append(ErrorPattern(
                    pattern=pattern["pattern"],
                    frequency=len(examples),
                    severity=pattern["severity"],
                    context=pattern["context"],
                    examples=examples[:3],  # Limit to 3 examples
                    solutions=pattern["solutions"]
                ))
        
        # Use LLM for deeper analysis
        analysis = await self.llm.agenerate([{
            "role": "user",
            "content": self.analysis_prompt.format(
                log_text=log_text,
                patterns=patterns
            )
        }])
        
        result = json.loads(analysis.generations[0].text)
        
        # Create LogAnalysis object
        return LogAnalysis(
            patterns=patterns,
            error_types=result["error_types"],
            root_causes=result["root_causes"],
            recommendations=result["recommendations"],
            severity=result["severity"],
            summary=result["summary"]
        )
    
    @cache.cached("known_patterns")
    async def _get_known_patterns(self) -> List[Dict[str, Any]]:
        """Get known error patterns from cache/database."""
        # In a real implementation, this would load from a database
        return [
            {
                "pattern": r"OutOfMemoryError",
                "severity": "high",
                "context": "JVM heap space",
                "solutions": [
                    "Increase heap size (-Xmx)",
                    "Check for memory leaks",
                    "Enable GC logging"
                ]
            },
            {
                "pattern": r"Connection refused",
                "severity": "medium",
                "context": "Network connectivity",
                "solutions": [
                    "Check service availability",
                    "Verify network settings",
                    "Check firewall rules"
                ]
            },
            {
                "pattern": r"Permission denied",
                "severity": "high",
                "context": "File system access",
                "solutions": [
                    "Check file permissions",
                    "Verify user access",
                    "Update security settings"
                ]
            }
        ]
    
    @handle_errors()
    async def _create_ticket(
        self,
        analysis: LogAnalysis,
        system: str = "jira"
    ) -> Dict[str, Any]:
        """Create a ticket in the issue tracking system.
        
        Args:
            analysis: Log analysis results
            system: Issue tracking system to use
            
        Returns:
            Ticket creation result
        """
        # Prepare ticket data
        ticket = {
            "title": f"Build Error: {analysis.error_types[0]}",
            "description": f"""
Build Error Analysis

Summary:
{analysis.summary}

Error Types:
{', '.join(analysis.error_types)}

Root Causes:
{', '.join(analysis.root_causes)}

Recommendations:
{', '.join(analysis.recommendations)}

Error Patterns:
{', '.join(p.pattern for p in analysis.patterns)}

Severity: {analysis.severity}
""",
            "severity": analysis.severity,
            "labels": ["jenkins", "build-error"] + analysis.error_types
        }
        
        # Create ticket in the appropriate system
        if system == "jira":
            return await self._create_jira_ticket(ticket)
        elif system == "github":
            return await self._create_github_issue(ticket)
        else:
            raise ValueError(f"Unsupported ticket system: {system}")
    
    async def _create_jira_ticket(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Jira ticket."""
        # This would use the Jira API in a real implementation
        return {
            "status": "created",
            "system": "jira",
            "ticket": ticket
        }
    
    async def _create_github_issue(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """Create a GitHub issue."""
        # This would use the GitHub API in a real implementation
        return {
            "status": "created",
            "system": "github",
            "ticket": ticket
        }
    
    @handle_errors()
    async def _get_solutions(
        self,
        error_pattern: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Get solution recommendations for an error pattern.
        
        Args:
            error_pattern: Error pattern to find solutions for
            context: Optional solution context
            
        Returns:
            List of solution recommendations
        """
        # Get solutions from known patterns
        known_patterns = await self._get_known_patterns()
        for pattern in known_patterns:
            if re.search(pattern["pattern"], error_pattern):
                return pattern["solutions"]
        
        # Use LLM for unknown patterns
        response = await self.llm.agenerate([{
            "role": "user",
            "content": f"""
Suggest solutions for this Jenkins build error:
{error_pattern}

Context:
{json.dumps(context) if context else 'No additional context'}

Format your response as a JSON list of solution strings.
"""
        }])
        
        return json.loads(response.generations[0].text)
    
    @handle_errors()
    async def _update_knowledge_base(
        self,
        pattern: str,
        solutions: List[str],
        severity: str = "medium",
        context: str = ""
    ) -> Dict[str, Any]:
        """Update the error pattern knowledge base.
        
        Args:
            pattern: Error pattern to add/update
            solutions: Solution recommendations
            severity: Error severity
            context: Error context
            
        Returns:
            Update status
        """
        known_patterns = await self._get_known_patterns()
        
        # Update existing pattern
        for p in known_patterns:
            if p["pattern"] == pattern:
                p["solutions"] = solutions
                p["severity"] = severity
                p["context"] = context
                await cache.set("known_patterns", known_patterns)
                return {
                    "status": "updated",
                    "pattern": pattern
                }
        
        # Add new pattern
        known_patterns.append({
            "pattern": pattern,
            "solutions": solutions,
            "severity": severity,
            "context": context
        })
        await cache.set("known_patterns", known_patterns)
        
        return {
            "status": "added",
            "pattern": pattern
        }
    
    async def handle_task(self, task: str) -> Dict[str, Any]:
        """Handle log analysis tasks.
        
        Args:
            task: Description of the analysis task
            
        Returns:
            Analysis results
        """
        task_lower = task.lower()
        
        if "analyze" in task_lower:
            return await self._handle_log_analysis(task)
        elif "ticket" in task_lower or "issue" in task_lower:
            return await self._handle_ticket_creation(task)
        elif "solution" in task_lower:
            return await self._handle_solution_request(task)
        elif "pattern" in task_lower or "knowledge" in task_lower:
            return await self._handle_pattern_update(task)
        else:
            return {
                "status": "error",
                "error": "Unsupported log analysis task",
                "task": task
            }
    
    async def _handle_log_analysis(self, task: str) -> Dict[str, Any]:
        """Handle log analysis requests."""
        # Extract log text from task
        # In a real implementation, this would parse the task more intelligently
        log_text = task.split("analyze")[-1].strip()
        
        analysis = await self._analyze_log(log_text)
        return {
            "status": "success",
            "analysis": {
                "patterns": [vars(p) for p in analysis.patterns],
                "error_types": analysis.error_types,
                "root_causes": analysis.root_causes,
                "recommendations": analysis.recommendations,
                "severity": analysis.severity,
                "summary": analysis.summary
            }
        }
    
    async def _handle_ticket_creation(self, task: str) -> Dict[str, Any]:
        """Handle ticket creation requests."""
        # Extract analysis from task context
        # In a real implementation, this would parse the task more intelligently
        if "analysis" not in task:
            return {
                "status": "error",
                "error": "No analysis provided for ticket creation",
                "task": task
            }
        
        # Create ticket
        system = "jira"  # Default to Jira
        if "github" in task.lower():
            system = "github"
        
        return await self._create_ticket(
            LogAnalysis(**json.loads(task.split("analysis")[-1].strip())),
            system
        )
    
    async def _handle_solution_request(self, task: str) -> Dict[str, Any]:
        """Handle solution request."""
        # Extract error pattern from task
        error_pattern = task.split("solution")[-1].strip()
        
        solutions = await self._get_solutions(error_pattern)
        return {
            "status": "success",
            "error_pattern": error_pattern,
            "solutions": solutions
        }
    
    async def _handle_pattern_update(self, task: str) -> Dict[str, Any]:
        """Handle pattern knowledge base update."""
        # Extract pattern details from task
        # In a real implementation, this would parse the task more intelligently
        parts = task.split()
        pattern = parts[parts.index("pattern") + 1]
        solutions = []
        severity = "medium"
        context = ""
        
        if "solutions" in task:
            solutions_text = task[task.index("solutions"):].split(":")[1].strip()
            solutions = [s.strip() for s in solutions_text.split(",")]
        
        if "severity" in task:
            severity = task[task.index("severity"):].split(":")[1].strip()
        
        if "context" in task:
            context = task[task.index("context"):].split(":")[1].strip()
        
        return await self._update_knowledge_base(
            pattern,
            solutions,
            severity,
            context
        )

# Global instance
log_analyzer = EnhancedLogAnalyzer()