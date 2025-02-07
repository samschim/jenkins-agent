"""Base agent class for Jenkins agents."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from langchain.agents import Tool
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from ..config.config import config

class BaseAgent(ABC):
    """Base class for all Jenkins agents."""
    
    def __init__(self, tools: List[Tool]):
        """Initialize the agent with tools.
        
        Args:
            tools: List of LangChain tools for the agent
        """
        self.tools = tools
        self.llm = ChatOpenAI(
            model=config.llm.model,
            temperature=config.llm.temperature
        )
        self.agent = initialize_agent(
            tools=tools,
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )
    
    @abstractmethod
    async def handle_task(self, task: str) -> Dict[str, Any]:
        """Handle a task assigned to the agent.
        
        Args:
            task: Description of the task to perform
            
        Returns:
            Result of the task execution
        """
        pass
    
    async def run(self, task: str) -> Dict[str, Any]:
        """Run the agent on a task.
        
        Args:
            task: Description of the task to perform
            
        Returns:
            Result of the task execution
        """
        try:
            return await self.handle_task(task)
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "task": task
            }