"""Log analyzer agent for analyzing Jenkins build logs."""
from typing import Dict, Any, List
from langchain.tools import Tool
from .base_agent import BaseAgent
from ..tools.jenkins_api import JenkinsAPI
from ..tools.log_analysis import LogAnalyzer

class LogAnalyzerAgent(BaseAgent):
    """Agent for analyzing Jenkins build logs."""
    
    def __init__(self):
        """Initialize log analyzer agent with required tools."""
        self.jenkins = JenkinsAPI()
        self.log_analyzer = LogAnalyzer()
        
        tools = [
            Tool(
                name="GetBuildLog",
                func=self.jenkins.get_build_log,
                description="Get the console log for a build"
            ),
            Tool(
                name="AnalyzeBuildLog",
                func=self.log_analyzer.analyze_build_log,
                description="Analyze a build log for errors and insights"
            ),
            Tool(
                name="SummarizeBuildLogs",
                func=self.log_analyzer.summarize_build_logs,
                description="Summarize multiple build logs to identify patterns"
            )
        ]
        
        super().__init__(tools)
    
    async def handle_task(self, task: str) -> Dict[str, Any]:
        """Handle log analysis tasks.
        
        Args:
            task: Description of the log analysis task to perform
            
        Returns:
            Result of the log analysis
        """
        if "analyze" in task.lower():
            return await self._handle_log_analysis(task)
        elif "pattern" in task.lower() or "summarize" in task.lower():
            return await self._handle_log_patterns(task)
        else:
            return {
                "status": "error",
                "error": "Unsupported log analysis task",
                "task": task
            }
    
    async def _handle_log_analysis(self, task: str) -> Dict[str, Any]:
        """Handle single log analysis requests.
        
        Args:
            task: Log analysis task description
            
        Returns:
            Log analysis results
        """
        # Extract job name from task
        words = task.split()
        job_name = next(
            (word for word in words if "job" not in word.lower()),
            None
        )
        
        if not job_name:
            return {
                "status": "error",
                "error": "No job name specified",
                "task": task
            }
        
        try:
            # Get the build log
            log_text = await self.jenkins.get_build_log(job_name)
            
            # Analyze the log
            analysis = await self.log_analyzer.analyze_build_log(log_text)
            
            return {
                "status": "success",
                "job": job_name,
                "analysis": analysis
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "job": job_name
            }
    
    async def _handle_log_patterns(self, task: str) -> Dict[str, Any]:
        """Handle pattern analysis across multiple logs.
        
        Args:
            task: Log pattern analysis task description
            
        Returns:
            Pattern analysis results
        """
        # Extract job name and number of builds to analyze
        words = task.split()
        job_name = next(
            (word for word in words if "job" not in word.lower()),
            None
        )
        
        # Try to find number of builds to analyze
        num_builds = 5  # default
        for word in words:
            if word.isdigit():
                num_builds = int(word)
                break
        
        if not job_name:
            return {
                "status": "error",
                "error": "No job name specified",
                "task": task
            }
        
        try:
            # Get job info to find recent builds
            job_info = await self.jenkins.get_job_info(job_name)
            recent_builds = job_info.get("builds", [])[:num_builds]
            
            # Collect logs for each build
            logs = []
            for build in recent_builds:
                build_number = build["number"]
                log_text = await self.jenkins.get_build_log(
                    job_name,
                    str(build_number)
                )
                logs.append({
                    "build_number": build_number,
                    "log_text": log_text
                })
            
            # Analyze patterns across logs
            patterns = await self.log_analyzer.summarize_build_logs(logs)
            
            return {
                "status": "success",
                "job": job_name,
                "num_builds_analyzed": len(logs),
                "patterns": patterns
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "job": job_name
            }