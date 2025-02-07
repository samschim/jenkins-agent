"""Supervisor agent for coordinating Jenkins agents."""
from typing import Dict, Any, Type
from .base_agent import BaseAgent
from .build_manager import BuildManagerAgent
from .log_analyzer import LogAnalyzerAgent
from .pipeline_manager import PipelineManagerAgent
from .plugin_manager import PluginManagerAgent
from .user_manager import UserManagerAgent

class SupervisorAgent:
    """Supervisor agent that coordinates specialized Jenkins agents."""
    
    def __init__(self):
        """Initialize supervisor with specialized agents."""
        self.agents = {
            "build": BuildManagerAgent(),
            "log": LogAnalyzerAgent(),
            "pipeline": PipelineManagerAgent(),
            "plugin": PluginManagerAgent(),
            "user": UserManagerAgent()
        }
    
    def _determine_agent(self, task: str) -> str:
        """Determine which agent should handle a task.
        
        Args:
            task: Task description
            
        Returns:
            Agent type that should handle the task
        """
        task_lower = task.lower()
        
        # Check for build-related tasks
        if any(word in task_lower for word in ["build", "trigger", "start"]):
            return "build"
        
        # Check for log-related tasks
        if any(word in task_lower for word in ["log", "error", "analyze"]):
            return "log"
        
        # Check for pipeline-related tasks
        if any(word in task_lower for word in ["pipeline", "stage", "workflow"]):
            return "pipeline"
        
        # Check for plugin-related tasks
        if any(word in task_lower for word in ["plugin", "install", "update"]):
            return "plugin"
        
        # Check for user-related tasks
        if any(word in task_lower for word in ["user", "permission", "role"]):
            return "user"
        
        # Default to build manager if unclear
        return "build"
    
    async def handle_task(self, task: str) -> Dict[str, Any]:
        """Handle a task by routing it to the appropriate agent.
        
        Args:
            task: Task description
            
        Returns:
            Result of the task execution
        """
        try:
            # Determine which agent should handle the task
            agent_type = self._determine_agent(task)
            agent = self.agents[agent_type]
            
            # Have the agent handle the task
            result = await agent.handle_task(task)
            
            # Add metadata about which agent handled it
            result["agent_type"] = agent_type
            
            return result
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "task": task,
                "agent_type": "supervisor"
            }
    
    async def handle_complex_task(self, task: str) -> Dict[str, Any]:
        """Handle a complex task that might require multiple agents.
        
        Args:
            task: Complex task description
            
        Returns:
            Combined results from multiple agents
        """
        task_lower = task.lower()
        results = {}
        
        try:
            # Check if we need build information
            if any(word in task_lower for word in ["build", "trigger", "start"]):
                results["build"] = await self.agents["build"].handle_task(task)
            
            # Check if we need log analysis
            if any(word in task_lower for word in ["log", "error", "analyze"]):
                results["log"] = await self.agents["log"].handle_task(task)
            
            # Check if we need pipeline information
            if any(word in task_lower for word in ["pipeline", "stage", "workflow"]):
                results["pipeline"] = await self.agents["pipeline"].handle_task(task)
            
            # If no specific agents were triggered, use the default agent
            if not results:
                agent_type = self._determine_agent(task)
                results[agent_type] = await self.agents[agent_type].handle_task(task)
            
            return {
                "status": "success",
                "results": results,
                "task": task
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "task": task,
                "agent_type": "supervisor"
            }