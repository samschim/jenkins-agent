"""Enhanced pipeline manager agent for Jenkins."""
from typing import Dict, Any, List
from langchain.tools import Tool
from .base_agent import BaseAgent
from ..tools.jenkins_api import JenkinsAPI
from ..tools.pipeline_generator import PipelineGenerator
from ..tools.pipeline_security import SecurityScanner

class EnhancedPipelineManager(BaseAgent):
    """Enhanced agent for managing Jenkins pipelines."""
    
    def __init__(self):
        """Initialize pipeline manager with tools."""
        self.jenkins = JenkinsAPI()
        self.generator = PipelineGenerator()
        self.security = SecurityScanner()
        
        tools = [
            Tool(
                name="GeneratePipeline",
                func=self._generate_pipeline,
                description="Generate a Jenkins pipeline for a project"
            ),
            Tool(
                name="ScanPipeline",
                func=self._scan_pipeline,
                description="Scan a pipeline for security issues"
            ),
            Tool(
                name="SecurePipeline",
                func=self._secure_pipeline,
                description="Enhance pipeline security"
            ),
            Tool(
                name="OptimizePipeline",
                func=self._optimize_pipeline,
                description="Optimize pipeline performance"
            ),
            Tool(
                name="ValidatePipeline",
                func=self._validate_pipeline,
                description="Validate pipeline configuration"
            )
        ]
        
        super().__init__(tools)
    
    async def _generate_pipeline(
        self,
        project_type: str,
        requirements: List[str]
    ) -> Dict[str, Any]:
        """Generate a pipeline for a project.
        
        Args:
            project_type: Type of project (java, python, node, docker)
            requirements: List of project requirements
            
        Returns:
            Generated pipeline
        """
        return await self.generator.generate_pipeline(
            project_type=project_type,
            requirements=requirements,
            validate=True
        )
    
    async def _scan_pipeline(self, pipeline: str) -> Dict[str, Any]:
        """Scan a pipeline for security issues.
        
        Args:
            pipeline: Pipeline configuration
            
        Returns:
            Security scan results
        """
        return await self.security.scan_pipeline(pipeline)
    
    async def _secure_pipeline(self, pipeline: str) -> Dict[str, Any]:
        """Enhance pipeline security.
        
        Args:
            pipeline: Pipeline configuration
            
        Returns:
            Secured pipeline
        """
        return await self.security.secure_pipeline(pipeline)
    
    async def _optimize_pipeline(
        self,
        pipeline: str,
        project_type: str
    ) -> Dict[str, Any]:
        """Optimize pipeline performance.
        
        Args:
            pipeline: Pipeline configuration
            project_type: Type of project
            
        Returns:
            Optimized pipeline
        """
        return await self.generator.optimize_pipeline(
            pipeline=pipeline,
            project_type=project_type
        )
    
    async def _validate_pipeline(self, pipeline: str) -> Dict[str, Any]:
        """Validate pipeline configuration.
        
        Args:
            pipeline: Pipeline configuration
            
        Returns:
            Validation results
        """
        # First check security
        security_results = await self.security.scan_pipeline(pipeline)
        
        # Then validate with generator
        validation_results = await self.generator._validate_pipeline(pipeline)
        
        return {
            "status": "success",
            "security": security_results,
            "validation": validation_results,
            "valid": (
                validation_results.get("valid", False) and
                security_results["analysis"]["security_score"] >= 80
            )
        }
    
    async def handle_task(self, task: str) -> Dict[str, Any]:
        """Handle pipeline-related tasks.
        
        Args:
            task: Task description
            
        Returns:
            Task result
        """
        task_lower = task.lower()
        
        try:
            # Generate new pipeline
            if "create" in task_lower or "new" in task_lower:
                # Extract project type and requirements
                project_type = self._extract_project_type(task)
                requirements = self._extract_requirements(task)
                
                return await self._generate_pipeline(
                    project_type=project_type,
                    requirements=requirements
                )
            
            # Scan pipeline
            elif "scan" in task_lower or "check" in task_lower:
                pipeline = await self._get_pipeline(task)
                return await self._scan_pipeline(pipeline)
            
            # Secure pipeline
            elif "secure" in task_lower:
                pipeline = await self._get_pipeline(task)
                return await self._secure_pipeline(pipeline)
            
            # Optimize pipeline
            elif "optimize" in task_lower:
                pipeline = await self._get_pipeline(task)
                project_type = self._extract_project_type(task)
                return await self._optimize_pipeline(
                    pipeline=pipeline,
                    project_type=project_type
                )
            
            # Validate pipeline
            elif "validate" in task_lower:
                pipeline = await self._get_pipeline(task)
                return await self._validate_pipeline(pipeline)
            
            else:
                return {
                    "status": "error",
                    "error": "Unsupported pipeline task",
                    "task": task
                }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "task": task
            }
    
    def _extract_project_type(self, task: str) -> str:
        """Extract project type from task description."""
        task_lower = task.lower()
        
        if "java" in task_lower:
            return "java"
        elif "python" in task_lower:
            return "python"
        elif "node" in task_lower or "javascript" in task_lower:
            return "node"
        elif "docker" in task_lower:
            return "docker"
        else:
            return "java"  # Default to Java
    
    def _extract_requirements(self, task: str) -> List[str]:
        """Extract requirements from task description."""
        requirements = []
        
        # Basic requirements
        if "test" in task.lower():
            requirements.append("Include testing stage")
        if "deploy" in task.lower():
            requirements.append("Include deployment stage")
        if "docker" in task.lower():
            requirements.append("Include Docker build")
        if "coverage" in task.lower():
            requirements.append("Include code coverage")
        
        return requirements
    
    async def _get_pipeline(self, task: str) -> str:
        """Get pipeline configuration from task description."""
        # Extract job name from task
        words = task.split()
        job_name = next(
            (word for word in words if "pipeline" not in word.lower()),
            None
        )
        
        if not job_name:
            raise ValueError("No pipeline name specified")
        
        # Get pipeline configuration
        job_info = await self.jenkins.get_job_info(job_name)
        if "config" not in job_info:
            raise ValueError(f"No pipeline configuration found for {job_name}")
        
        return job_info["config"]