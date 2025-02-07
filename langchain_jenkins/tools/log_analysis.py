"""Log analysis tools for LangChain agents."""
from typing import List, Dict, Any
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from ..config.config import config

class LogAnalyzer:
    """Analyzes Jenkins build logs using LLM."""
    
    def __init__(self):
        """Initialize log analyzer with LLM."""
        self.llm = ChatOpenAI(
            model=config.llm.model,
            temperature=config.llm.temperature
        )
    
    async def analyze_build_log(self, log_text: str) -> Dict[str, Any]:
        """Analyze a build log for errors and insights.
        
        Args:
            log_text: The build log text to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        # Create a prompt for the LLM to analyze the log
        prompt = f"""Analyze this Jenkins build log and provide:
1. Build status (success/failure)
2. Any errors found
3. Root cause analysis if failed
4. Recommendations for fixes

Build Log:
{log_text[:4000]}  # Limit log size for token constraints

Provide the analysis in JSON format with these keys:
- status: "success" or "failure"
- errors: list of error messages found
- root_cause: explanation of the root cause if failed
- recommendations: list of suggested fixes
"""
        
        # Get analysis from LLM
        response = await self.llm.agenerate([HumanMessage(content=prompt)])
        
        try:
            # Parse the response into structured format
            analysis = eval(response.generations[0][0].text)
            return analysis
        except Exception as e:
            return {
                "status": "unknown",
                "errors": [f"Failed to analyze log: {str(e)}"],
                "root_cause": "Log analysis failed",
                "recommendations": ["Try analyzing the log manually"]
            }
    
    async def summarize_build_logs(
        self,
        logs: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Summarize multiple build logs to identify patterns.
        
        Args:
            logs: List of dictionaries containing build logs
                 Each dict should have 'build_number' and 'log_text' keys
                 
        Returns:
            Summary of patterns and insights found across logs
        """
        # Create a prompt for the LLM to analyze multiple logs
        logs_summary = "\n".join(
            f"Build #{log['build_number']}: {log['log_text'][:500]}..."
            for log in logs
        )
        
        prompt = f"""Analyze these Jenkins build logs and identify:
1. Common patterns in failures
2. Success rate
3. Recurring issues
4. Trends over time

Build Logs:
{logs_summary}

Provide the analysis in JSON format with these keys:
- patterns: list of common patterns found
- success_rate: percentage of successful builds
- recurring_issues: list of issues that appear multiple times
- trends: observations about changes over time
"""
        
        # Get analysis from LLM
        response = await self.llm.agenerate([HumanMessage(content=prompt)])
        
        try:
            # Parse the response into structured format
            analysis = eval(response.generations[0][0].text)
            return analysis
        except Exception as e:
            return {
                "patterns": [],
                "success_rate": 0,
                "recurring_issues": [f"Analysis failed: {str(e)}"],
                "trends": []
            }