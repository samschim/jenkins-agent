"""Pipeline manager agent for handling Jenkins pipelines."""
from typing import Dict, Any, List
from langchain.tools import Tool
from .base_agent import BaseAgent
from ..tools.jenkins_api import JenkinsAPI
from ..tools.pipeline_tools import PipelineTools

class PipelineManagerAgent(BaseAgent):
    """Agent for managing Jenkins pipelines."""
    
    def __init__(self):
        """Initialize pipeline manager agent with required tools."""
        self.jenkins = JenkinsAPI()
        self.pipeline_tools = PipelineTools()
        
        tools = [
            Tool(
                name="GetPipelineStatus",
                func=self.pipeline_tools.get_pipeline_status,
                description="Get the status of a pipeline"
            ),
            Tool(
                name="GetPipelineStages",
                func=self.pipeline_tools.get_pipeline_stages,
                description="Get information about pipeline stages"
            ),
            Tool(
                name="GetPipelineDefinition",
                func=self.pipeline_tools.get_pipeline_definition,
                description="Get the Jenkinsfile content for a pipeline"
            ),
            Tool(
                name="UpdatePipelineDefinition",
                func=self.pipeline_tools.update_pipeline_definition,
                description="Update the Jenkinsfile content for a pipeline"
            ),
            Tool(
                name="AnalyzePipelinePerformance",
                func=self.pipeline_tools.analyze_pipeline_performance,
                description="Analyze pipeline performance across multiple builds"
            )
        ]
        
        super().__init__(tools)
    
    async def handle_task(self, task: str) -> Dict[str, Any]:
        """Handle pipeline-related tasks.
        
        Args:
            task: Description of the pipeline task to perform
            
        Returns:
            Result of the task execution
        """
        if "status" in task.lower():
            return await self._handle_pipeline_status(task)
        elif "stage" in task.lower():
            return await self._handle_pipeline_stages(task)
        elif "performance" in task.lower() or "analyze" in task.lower():
            return await self._handle_pipeline_performance(task)
        elif "update" in task.lower() or "modify" in task.lower():
            return await self._handle_pipeline_update(task)
        else:
            return {
                "status": "error",
                "error": "Unsupported pipeline task",
                "task": task
            }
    
    async def _handle_pipeline_status(self, task: str) -> Dict[str, Any]:
        """Handle pipeline status requests.
        
        Args:
            task: Pipeline status task description
            
        Returns:
            Pipeline status information
        """
        # Extract pipeline name from task
        words = task.split()
        pipeline_name = next(
            (word for word in words if "pipeline" not in word.lower()),
            None
        )
        
        if not pipeline_name:
            return {
                "status": "error",
                "error": "No pipeline name specified",
                "task": task
            }
        
        try:
            status = await self.pipeline_tools.get_pipeline_status(pipeline_name)
            return {
                "status": "success",
                "pipeline": pipeline_name,
                "pipeline_status": status
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "pipeline": pipeline_name
            }
    
    async def _handle_pipeline_stages(self, task: str) -> Dict[str, Any]:
        """Handle pipeline stages requests.
        
        Args:
            task: Pipeline stages task description
            
        Returns:
            Pipeline stages information
        """
        # Extract pipeline name from task
        words = task.split()
        pipeline_name = next(
            (word for word in words if "pipeline" not in word.lower()),
            None
        )
        
        if not pipeline_name:
            return {
                "status": "error",
                "error": "No pipeline name specified",
                "task": task
            }
        
        try:
            stages = await self.pipeline_tools.get_pipeline_stages(pipeline_name)
            return {
                "status": "success",
                "pipeline": pipeline_name,
                "stages": stages
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "pipeline": pipeline_name
            }
    
    async def _handle_pipeline_performance(self, task: str) -> Dict[str, Any]:
        """Handle pipeline performance analysis requests.
        
        Args:
            task: Pipeline performance task description
            
        Returns:
            Pipeline performance analysis
        """
        # Extract pipeline name and number of builds to analyze
        words = task.split()
        pipeline_name = next(
            (word for word in words if "pipeline" not in word.lower()),
            None
        )
        
        # Try to find number of builds to analyze
        num_builds = 10  # default
        for word in words:
            if word.isdigit():
                num_builds = int(word)
                break
        
        if not pipeline_name:
            return {
                "status": "error",
                "error": "No pipeline name specified",
                "task": task
            }
        
        try:
            analysis = await self.pipeline_tools.analyze_pipeline_performance(
                pipeline_name,
                num_builds
            )
            return {
                "status": "success",
                "pipeline": pipeline_name,
                "num_builds_analyzed": num_builds,
                "performance_analysis": analysis
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "pipeline": pipeline_name
            }
    
    async def _handle_pipeline_update(self, task: str) -> Dict[str, Any]:
        """Handle pipeline definition update requests.
        
        Args:
            task: Pipeline update task description
            
        Returns:
            Pipeline update results
        """
        # This is a simplified implementation
        # In a real system, you'd want more sophisticated parsing of the update request
        words = task.split()
        pipeline_name = next(
            (word for word in words if "pipeline" not in word.lower()),
            None
        )
        
        if not pipeline_name:
            return {
                "status": "error",
                "error": "No pipeline name specified",
                "task": task
            }
        
        try:
            # First get the current definition
            current_def = await self.pipeline_tools.get_pipeline_definition(
                pipeline_name
            )
            
            # Here you would typically parse the task to understand what updates
            # are needed and modify the definition accordingly
            # For now, we'll just return the current definition
            
            return {
                "status": "success",
                "pipeline": pipeline_name,
                "current_definition": current_def,
                "message": "Pipeline update not implemented yet"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "pipeline": pipeline_name
            }