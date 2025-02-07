"""Enhanced Build Manager Agent with advanced features.

Features:
- Build start/stop/restart
- Build history retrieval
- Dependency management
- Priority setting
- Status monitoring
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio
from langchain.tools import Tool
from .base_agent import BaseAgent
from ..tools.jenkins_api import JenkinsAPI
from ..tools.log_analysis import LogAnalyzer
from ..utils.cache import cache
from ..utils.error_handler import handle_errors

@dataclass
class BuildInfo:
    """Build information."""
    number: int
    status: str
    timestamp: datetime
    duration: int
    result: str
    url: str
    changes: List[Dict[str, Any]]
    artifacts: List[Dict[str, Any]]

class EnhancedBuildManagerAgent(BaseAgent):
    """Enhanced agent for managing Jenkins builds."""
    
    def __init__(self):
        """Initialize build manager agent with enhanced tools."""
        self.jenkins = JenkinsAPI()
        self.log_analyzer = LogAnalyzer()
        
        tools = [
            Tool(
                name="StartBuild",
                func=self._start_build,
                description="Start a Jenkins build with optional parameters and priority"
            ),
            Tool(
                name="StopBuild",
                func=self._stop_build,
                description="Stop a running Jenkins build"
            ),
            Tool(
                name="RestartBuild",
                func=self._restart_build,
                description="Restart a Jenkins build"
            ),
            Tool(
                name="GetBuildStatus",
                func=self._get_build_status,
                description="Get the status of a Jenkins build"
            ),
            Tool(
                name="GetBuildHistory",
                func=self._get_build_history,
                description="Get the build history of a Jenkins job"
            ),
            Tool(
                name="ManageDependencies",
                func=self._manage_dependencies,
                description="Manage upstream and downstream job dependencies"
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
    
    @handle_errors()
    async def _start_build(
        self,
        job_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        priority: Optional[str] = None
    ) -> Dict[str, Any]:
        """Start a Jenkins build.
        
        Args:
            job_name: Name of the job
            parameters: Optional build parameters
            priority: Optional build priority (high, medium, low)
            
        Returns:
            Build information
        """
        # Set QueueItem priority if specified
        if priority:
            await self.jenkins.post(
                f"/queue/item/{job_name}/setPriority",
                {"priority": priority}
            )
        
        # Start build
        response = await self.jenkins.build_job(job_name, parameters)
        
        return {
            "status": "started",
            "job": job_name,
            "queue_number": response.get("queueNumber"),
            "priority": priority
        }
    
    @handle_errors()
    async def _stop_build(
        self,
        job_name: str,
        build_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """Stop a running build.
        
        Args:
            job_name: Name of the job
            build_number: Optional build number (defaults to last build)
            
        Returns:
            Stop status
        """
        if not build_number:
            status = await self._get_build_status(job_name)
            build_number = status.get("number")
        
        response = await self.jenkins.post(
            f"/job/{job_name}/{build_number}/stop"
        )
        
        return {
            "status": "stopped",
            "job": job_name,
            "build": build_number
        }
    
    @handle_errors()
    async def _restart_build(
        self,
        job_name: str,
        build_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """Restart a Jenkins build.
        
        Args:
            job_name: Name of the job
            build_number: Optional build number (defaults to last build)
            
        Returns:
            Restart status
        """
        # Stop the build if it's running
        await self._stop_build(job_name, build_number)
        
        # Start a new build
        return await self._start_build(job_name)
    
    @cache.cached("build_status")
    async def _get_build_status(
        self,
        job_name: str,
        build_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get build status.
        
        Args:
            job_name: Name of the job
            build_number: Optional build number (defaults to last build)
            
        Returns:
            Build status
        """
        return await self.jenkins.get_job_info(job_name, build_number)
    
    @handle_errors()
    async def _get_build_history(
        self,
        job_name: str,
        limit: int = 5
    ) -> List[BuildInfo]:
        """Get build history.
        
        Args:
            job_name: Name of the job
            limit: Number of builds to retrieve
            
        Returns:
            List of build information
        """
        response = await self.jenkins.get(
            f"/job/{job_name}/api/json?tree=builds[number,status,timestamp,duration,result,url,changeSet[items[*]],artifacts[*]]&depth=2"
        )
        
        builds = []
        for build in response.get("builds", [])[:limit]:
            builds.append(BuildInfo(
                number=build["number"],
                status=build.get("status", "unknown"),
                timestamp=datetime.fromtimestamp(build["timestamp"] / 1000),
                duration=build["duration"],
                result=build.get("result", "unknown"),
                url=build["url"],
                changes=build.get("changeSet", {}).get("items", []),
                artifacts=build.get("artifacts", [])
            ))
        
        return builds
    
    @handle_errors()
    async def _manage_dependencies(
        self,
        job_name: str,
        upstream_jobs: Optional[List[str]] = None,
        downstream_jobs: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Manage build dependencies.
        
        Args:
            job_name: Name of the job
            upstream_jobs: Optional list of upstream job names
            downstream_jobs: Optional list of downstream job names
            
        Returns:
            Updated dependency configuration
        """
        config = await self.jenkins.get(f"/job/{job_name}/config.xml")
        
        # Update upstream jobs
        if upstream_jobs:
            upstream_config = "<upstreamProjects>" + ",".join(upstream_jobs) + "</upstreamProjects>"
            config = config.replace("<upstreamProjects/>", upstream_config)
        
        # Update downstream jobs
        if downstream_jobs:
            downstream_config = "<downstreamProjects>" + ",".join(downstream_jobs) + "</downstreamProjects>"
            config = config.replace("<downstreamProjects/>", downstream_config)
        
        # Update configuration
        await self.jenkins.post(
            f"/job/{job_name}/config.xml",
            config
        )
        
        return {
            "status": "updated",
            "job": job_name,
            "upstream_jobs": upstream_jobs,
            "downstream_jobs": downstream_jobs
        }
    
    async def handle_task(self, task: str) -> Dict[str, Any]:
        """Handle build-related tasks.
        
        Args:
            task: Description of the build task to perform
            
        Returns:
            Result of the task execution
        """
        # Parse the task to determine the action needed
        task_lower = task.lower()
        
        if "start" in task_lower or "trigger" in task_lower:
            return await self._handle_build_trigger(task)
        elif "stop" in task_lower:
            return await self._handle_build_stop(task)
        elif "restart" in task_lower:
            return await self._handle_build_restart(task)
        elif "status" in task_lower:
            return await self._handle_build_status(task)
        elif "history" in task_lower:
            return await self._handle_build_history(task)
        elif "dependency" in task_lower:
            return await self._handle_dependency_management(task)
        elif "log" in task_lower:
            return await self._handle_build_log(task)
        else:
            return {
                "status": "error",
                "error": "Unsupported build task",
                "task": task
            }
    
    async def _handle_build_trigger(self, task: str) -> Dict[str, Any]:
        """Handle build trigger requests."""
        # Extract job name and parameters from task
        words = task.split()
        job_name = next(
            (word for word in words if "job" not in word.lower()),
            None
        )
        
        # Extract priority if specified
        priority = None
        if "priority" in task.lower():
            if "high" in task.lower():
                priority = "high"
            elif "medium" in task.lower():
                priority = "medium"
            elif "low" in task.lower():
                priority = "low"
        
        if not job_name:
            return {
                "status": "error",
                "error": "No job name specified",
                "task": task
            }
        
        return await self._start_build(job_name, priority=priority)
    
    async def _handle_build_stop(self, task: str) -> Dict[str, Any]:
        """Handle build stop requests."""
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
        
        return await self._stop_build(job_name)
    
    async def _handle_build_restart(self, task: str) -> Dict[str, Any]:
        """Handle build restart requests."""
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
        
        return await self._restart_build(job_name)
    
    async def _handle_build_status(self, task: str) -> Dict[str, Any]:
        """Handle build status requests."""
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
        
        return await self._get_build_status(job_name)
    
    async def _handle_build_history(self, task: str) -> Dict[str, Any]:
        """Handle build history requests."""
        words = task.split()
        job_name = next(
            (word for word in words if "job" not in word.lower()),
            None
        )
        
        # Extract limit if specified
        limit = 5
        for word in words:
            if word.isdigit():
                limit = int(word)
                break
        
        if not job_name:
            return {
                "status": "error",
                "error": "No job name specified",
                "task": task
            }
        
        history = await self._get_build_history(job_name, limit)
        return {
            "status": "success",
            "job": job_name,
            "history": [vars(build) for build in history]
        }
    
    async def _handle_dependency_management(self, task: str) -> Dict[str, Any]:
        """Handle dependency management requests."""
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
        
        # Extract upstream and downstream jobs
        upstream_jobs = []
        downstream_jobs = []
        
        if "upstream" in task.lower():
            # Extract jobs after "upstream"
            idx = words.index("upstream")
            while idx + 1 < len(words) and words[idx + 1] != "downstream":
                upstream_jobs.append(words[idx + 1])
                idx += 1
        
        if "downstream" in task.lower():
            # Extract jobs after "downstream"
            idx = words.index("downstream")
            while idx + 1 < len(words):
                downstream_jobs.append(words[idx + 1])
                idx += 1
        
        return await self._manage_dependencies(
            job_name,
            upstream_jobs or None,
            downstream_jobs or None
        )
    
    async def _handle_build_log(self, task: str) -> Dict[str, Any]:
        """Handle build log requests."""
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
        
        # Get the build log
        log_text = await self.jenkins.get_build_log(job_name)
        
        # Analyze the log if requested
        if "analyze" in task.lower():
            analysis = await self.log_analyzer.analyze_build_log(log_text)
            return {
                "status": "success",
                "job": job_name,
                "log": log_text,
                "analysis": analysis
            }
        
        return {
            "status": "success",
            "job": job_name,
            "log": log_text
        }

# Global instance
build_manager = EnhancedBuildManagerAgent()