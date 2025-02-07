"""Build manager agent for handling Jenkins builds."""
from typing import Dict, Any, List
from langchain.tools import Tool
from .base_agent import BaseAgent
from ..tools.jenkins_api import JenkinsAPI
from ..tools.log_analysis import LogAnalyzer

class BuildManagerAgent(BaseAgent):
    """Agent for managing Jenkins builds."""
    
    def __init__(self):
        """Initialize build manager agent with required tools."""
        self.jenkins = JenkinsAPI()
        self.log_analyzer = LogAnalyzer()
        
        tools = [
            Tool(
                name="TriggerBuild",
                func=self.jenkins.build_job,
                description="Trigger a Jenkins build for a job"
            ),
            Tool(
                name="GetBuildStatus",
                func=self.jenkins.get_job_info,
                description="Get the status of a Jenkins job"
            ),
            Tool(
                name="GetBuildLog",
                func=self.jenkins.get_build_log,
                description="Get the console log for a build"
            ),
            Tool(
                name="AnalyzeBuildLog",
                func=self.log_analyzer.analyze_build_log,
                description="Analyze a build log for errors and insights"
            )
        ]
        
        super().__init__(tools)
    
    async def handle_task(self, task: str) -> Dict[str, Any]:
        """Handle build-related tasks.
        
        Args:
            task: Description of the build task to perform
            
        Returns:
            Result of the task execution
        """
        # Parse the task to determine the action needed
        if "start" in task.lower() or "trigger" in task.lower():
            return await self._handle_build_trigger(task)
        elif "status" in task.lower():
            return await self._handle_build_status(task)
        elif "log" in task.lower():
            return await self._handle_build_log(task)
        else:
            return {
                "status": "error",
                "error": "Unsupported build task",
                "task": task
            }
    
    async def _handle_build_trigger(self, task: str) -> Dict[str, Any]:
        """Handle build trigger requests.
        
        Args:
            task: Build trigger task description
            
        Returns:
            Build trigger results
        """
        # Extract job name from task
        # This is a simple implementation - could be enhanced with better NLP
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
            result = await self.jenkins.build_job(job_name)
            return {
                "status": "success",
                "message": f"Build triggered for job {job_name}",
                "result": result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "job": job_name
            }
    
    async def _handle_build_status(self, task: str) -> Dict[str, Any]:
        """Handle build status requests.
        
        Args:
            task: Build status task description
            
        Returns:
            Build status information
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
            status = await self.jenkins.get_job_info(job_name)
            return {
                "status": "success",
                "job": job_name,
                "build_status": status
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "job": job_name
            }
    
    async def _handle_build_log(self, task: str) -> Dict[str, Any]:
        """Handle build log requests.
        
        Args:
            task: Build log task description
            
        Returns:
            Build log analysis
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
                "log_analysis": analysis
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "job": job_name
            }