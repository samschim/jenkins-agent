"""Supervisor agent for coordinating Jenkins agents."""
import time
from typing import Dict, Any, Type
from .base_agent import BaseAgent
from .build_manager import BuildManagerAgent
from .log_analyzer import LogAnalyzerAgent
from .pipeline_manager import PipelineManagerAgent
from .plugin_manager import PluginManagerAgent
from .user_manager import UserManagerAgent
from ..utils.embeddings import EmbeddingManager
from ..utils.metrics import MetricsCollector

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
        self.embedding_manager = EmbeddingManager()
        self.metrics_collector = MetricsCollector()
    
    async def _determine_agent(self, task: str) -> str:
        """Determine which agent should handle a task using embeddings.
        
        Args:
            task: Task description
            
        Returns:
            Agent type that should handle the task
        """
        # Use embedding manager to find best matching agent
        return await self.embedding_manager.find_best_agent(task)
    
    async def handle_task(
        self,
        task: str,
        agent_type: str = None
    ) -> Dict[str, Any]:
        """Handle a task by routing it to the appropriate agent.
        
        Args:
            task: Task description
            agent_type: Optional agent type to use
            
        Returns:
            Result of the task execution
        """
        try:
            # Use specified agent type or determine from task
            if not agent_type:
                agent_type = await self._determine_agent(task)
            
            # Validate agent type
            if agent_type not in self.agents:
                raise ValueError(f"Invalid agent type: {agent_type}")
            
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
                agent_type = await self._determine_agent(task)
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
    
    async def collect_metrics_and_insights(self) -> Dict[str, Any]:
        """Collect metrics and generate insights about the Jenkins system.
        
        Returns:
            Metrics and insights about the system
        """
        try:
            # Collect metrics
            metrics = await self.metrics_collector.collect_metrics()
            
            # Generate insights using LLM
            insights_prompt = f"""
            Analyze these Jenkins metrics and provide insights:
            
            Build Metrics:
            - Total Builds: {metrics['builds'].get('total_builds', 0)}
            - Success Rate: {metrics['builds'].get('successful_builds', 0) / max(metrics['builds'].get('total_builds', 1), 1) * 100:.1f}%
            - Average Duration: {metrics['builds'].get('average_duration', 0) / 60:.1f} minutes
            
            Pipeline Metrics:
            - Total Runs: {metrics['pipelines'].get('total_runs', 0)}
            - Success Rate: {metrics['pipelines'].get('successful_runs', 0) / max(metrics['pipelines'].get('total_runs', 1), 1) * 100:.1f}%
            - Average Duration: {metrics['pipelines'].get('average_duration', 0) / 60:.1f} minutes
            
            Provide:
            1. Key observations about system health
            2. Potential areas for improvement
            3. Recommendations for optimization
            """
            
            insights_result = await self.agents["log"].llm.agenerate([insights_prompt])
            insights = insights_result.generations[0][0].text
            
            return {
                "status": "success",
                "metrics": metrics,
                "insights": insights,
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "agent_type": "supervisor"
            }