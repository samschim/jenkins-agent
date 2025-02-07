"""Embedding utilities for LangChain agents."""
import numpy as np
from typing import List, Dict, Any
from langchain_community.embeddings import OpenAIEmbeddings
from ..config.config import config

class EmbeddingManager:
    """Manages embeddings for task routing and similarity matching."""
    
    def __init__(self):
        """Initialize embedding manager."""
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=config.llm.api_key,
            openai_api_base=config.llm.api_base
        )
        
        # Pre-defined capability embeddings for each agent type
        self.capability_embeddings = {
            "build": self._get_capability_embedding([
                "create build job", "trigger build", "configure build",
                "build parameters", "build status", "build history"
            ]),
            "log": self._get_capability_embedding([
                "analyze logs", "error analysis", "build output",
                "console log", "log patterns", "failure diagnosis"
            ]),
            "pipeline": self._get_capability_embedding([
                "pipeline definition", "stages", "jenkinsfile",
                "workflow", "pipeline status", "pipeline optimization"
            ]),
            "plugin": self._get_capability_embedding([
                "install plugin", "update plugin", "remove plugin",
                "plugin configuration", "plugin dependencies"
            ]),
            "user": self._get_capability_embedding([
                "user management", "permissions", "roles",
                "authentication", "authorization", "security"
            ])
        }
    
    async def _get_capability_embedding(self, capabilities: List[str]) -> np.ndarray:
        """Get embedding for a list of capabilities.
        
        Args:
            capabilities: List of capability descriptions
            
        Returns:
            Averaged embedding vector
        """
        # Combine capabilities into a single text
        text = " ".join(capabilities)
        
        # Get embedding
        embedding = await self.embeddings.aembed_query(text)
        return np.array(embedding)
    
    async def get_task_embedding(self, task: str) -> np.ndarray:
        """Get embedding for a task description.
        
        Args:
            task: Task description
            
        Returns:
            Task embedding vector
        """
        embedding = await self.embeddings.aembed_query(task)
        return np.array(embedding)
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score
        """
        return np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )
    
    async def find_best_agent(self, task: str) -> str:
        """Find the best agent for a given task.
        
        Args:
            task: Task description
            
        Returns:
            Best matching agent type
        """
        # Get task embedding
        task_embedding = await self.get_task_embedding(task)
        
        # Calculate similarity with each agent's capabilities
        similarities = {
            agent_type: self.calculate_similarity(
                task_embedding,
                self.capability_embeddings[agent_type]
            )
            for agent_type in self.capability_embeddings
        }
        
        # Return agent type with highest similarity
        return max(similarities.items(), key=lambda x: x[1])[0]