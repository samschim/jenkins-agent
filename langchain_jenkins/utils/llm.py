"""LLM utilities for Jenkins agent."""
import os
import json
from typing import Dict, Any, List
import httpx
from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from ..config.config import config

class LMStudio:
    """LM Studio API client."""
    
    def __init__(self):
        """Initialize LM Studio client."""
        self.url = os.getenv("LM_STUDIO_URL", "http://192.168.0.221:1234")
        self.client = httpx.AsyncClient(timeout=30.0)
        self.model = os.getenv("LM_STUDIO_MODEL", "llama-3.2-1b-instruct")
    
    async def generate(self, prompt: str, system_prompt: str = None) -> str:
        """Generate text using LM Studio.
        
        Args:
            prompt: Input prompt
            system_prompt: Optional system prompt
            
        Returns:
            Generated text response
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.post(
                f"{self.url}/v1/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            )
            response_data = await response.json()
            return response_data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error: {str(e)}"

class LLMManager:
    """Manager for LLM interactions."""
    
    def __init__(self):
        """Initialize LLM manager."""
        self.lm_studio = LMStudio()
    
    async def generate(
        self,
        prompt: str,
        system_prompt: str = None
    ) -> str:
        """Generate text using LM Studio.
        
        Args:
            prompt: Input prompt
            system_prompt: Optional system prompt
            
        Returns:
            Generated text
        """
        try:
            return await self.lm_studio.generate(prompt, system_prompt)
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def analyze_logs(self, logs: str) -> Dict[str, Any]:
        """Analyze build logs.
        
        Args:
            logs: Build logs
            
        Returns:
            Analysis results
        """
        system_prompt = """You are an expert at analyzing Jenkins build logs.
Identify errors, warnings, and potential issues.

Format your response as JSON with these keys:
- status: overall status (success/warning/error)
- issues: list of identified issues
- recommendations: list of recommendations
- severity: severity level (low/medium/high)"""
        
        try:
            response = await self.generate(logs, system_prompt)
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "status": "error",
                "issues": ["Failed to parse LLM response"],
                "recommendations": ["Try again or check logs manually"],
                "severity": "high"
            }
        except Exception as e:
            return {
                "status": "error",
                "issues": [str(e)],
                "recommendations": ["Try again later"],
                "severity": "high"
            }
    
    async def suggest_fixes(self, error: str) -> Dict[str, Any]:
        """Suggest fixes for build errors.
        
        Args:
            error: Build error
            
        Returns:
            Fix suggestions
        """
        system_prompt = """You are an expert at fixing Jenkins build errors.
Analyze the error and suggest potential fixes.

Format your response as JSON with these keys:
- error_type: type of error
- causes: list of potential causes
- solutions: list of suggested solutions
- confidence: confidence level (0-1)"""
        
        try:
            response = await self.generate(error, system_prompt)
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "error_type": "unknown",
                "causes": ["Failed to parse LLM response"],
                "solutions": ["Try again or analyze manually"],
                "confidence": 0.0
            }
        except Exception as e:
            return {
                "error_type": "error",
                "causes": [str(e)],
                "solutions": ["Try again later"],
                "confidence": 0.0
            }
    
    async def optimize_pipeline(self, pipeline: str) -> Dict[str, Any]:
        """Optimize Jenkins pipeline.
        
        Args:
            pipeline: Pipeline configuration
            
        Returns:
            Optimization suggestions
        """
        system_prompt = """You are an expert at optimizing Jenkins pipelines.
Analyze the pipeline and suggest improvements.

Format your response as JSON with these keys:
- issues: list of identified issues
- optimizations: list of suggested optimizations
- impact: expected impact (low/medium/high)
- risks: potential risks"""
        
        try:
            response = await self.generate(pipeline, system_prompt)
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "issues": ["Failed to parse LLM response"],
                "optimizations": ["Try again or optimize manually"],
                "impact": "unknown",
                "risks": ["Unknown due to parsing error"]
            }
        except Exception as e:
            return {
                "issues": [str(e)],
                "optimizations": ["Try again later"],
                "impact": "unknown",
                "risks": ["Error during analysis"]
            }

# Global instance
llm_manager = LLMManager()