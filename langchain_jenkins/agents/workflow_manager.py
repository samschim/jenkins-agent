"""Workflow Manager for coordinating agents using LangGraph.

Features:
- Graph-based agent coordination
- Dynamic task routing
- Inter-agent communication
- State management
"""
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import json
from langgraph.graph import StateGraph, END
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage
from .enhanced_build_manager import build_manager
from .enhanced_log_analyzer import log_analyzer
from .enhanced_pipeline_manager import pipeline_manager
from .enhanced_plugin_manager import plugin_manager
from ..config.config import config
from ..utils.cache import cache
from ..utils.error_handler import handle_errors

@dataclass
class AgentState:
    """Agent state information."""
    task: str
    agent_type: str
    status: str
    result: Optional[Dict[str, Any]] = None
    next_steps: List[str] = field(default_factory=list)
    history: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class WorkflowState:
    """Workflow state information."""
    task: str
    current_agent: str
    agents: Dict[str, AgentState]
    messages: List[Dict[str, Any]]
    artifacts: Dict[str, Any]

class WorkflowManager:
    """Manager for coordinating agent workflows."""
    
    def __init__(self):
        """Initialize workflow manager."""
        self.llm = ChatOpenAI(
            model=config.llm.model,
            temperature=0.1
        )
        
        # Create routing chain
        self.routing_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at routing Jenkins tasks to specialized agents.
Analyze this task and determine which agent should handle it.

Available agents:
- build_manager: Handles build operations
- log_analyzer: Handles log analysis
- pipeline_manager: Handles pipeline operations
- plugin_manager: Handles plugin management

Format your response as JSON with these keys:
- agent: name of the agent to handle the task
- reason: reason for selecting this agent
- subtasks: list of subtasks for other agents (if any)"""),
            ("human", "{task}")
        ])
        
        # Create coordination chain
        self.coordination_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at coordinating Jenkins agents.
Review the current workflow state and determine next steps.

Format your response as JSON with these keys:
- next_agent: next agent to run (or "end" if done)
- reason: reason for this decision
- coordination: list of coordination actions needed
- artifacts: list of artifacts to share"""),
            ("human", "{workflow_state}")
        ])
        
        # Initialize workflow graph
        self.graph = self._create_workflow_graph()
    
    def _create_workflow_graph(self) -> StateGraph:
        """Create workflow graph.
        
        Returns:
            StateGraph instance
        """
        # Create graph
        graph = StateGraph()
        
        # Add nodes
        graph.add_node("supervisor", self._supervisor_node)
        graph.add_node("build_manager", self._build_manager_node)
        graph.add_node("log_analyzer", self._log_analyzer_node)
        graph.add_node("pipeline_manager", self._pipeline_manager_node)
        graph.add_node("plugin_manager", self._plugin_manager_node)
        
        # Add edges with conditions
        graph.add_edge("supervisor", "build_manager", self._should_route_to_build)
        graph.add_edge("supervisor", "log_analyzer", self._should_route_to_logs)
        graph.add_edge("supervisor", "pipeline_manager", self._should_route_to_pipeline)
        graph.add_edge("supervisor", "plugin_manager", self._should_route_to_plugin)
        
        # Add coordination edges
        graph.add_edge("build_manager", "supervisor", self._needs_coordination)
        graph.add_edge("log_analyzer", "supervisor", self._needs_coordination)
        graph.add_edge("pipeline_manager", "supervisor", self._needs_coordination)
        graph.add_edge("plugin_manager", "supervisor", self._needs_coordination)
        
        # Add end condition
        graph.add_edge("supervisor", END, self._is_workflow_complete)
        
        # Set entry point
        graph.set_entry_point("supervisor")
        
        return graph
    
    async def _supervisor_node(
        self,
        state: WorkflowState,
        **kwargs
    ) -> WorkflowState:
        """Handle supervisor node logic.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        # Get routing decision
        response = await self.llm.agenerate([{
            "role": "user",
            "content": self.routing_prompt.format(task=state.task)
        }])
        
        routing = json.loads(response.generations[0].text)
        
        # Update state
        state.current_agent = routing["agent"]
        if routing["agent"] not in state.agents:
            state.agents[routing["agent"]] = AgentState(
                task=state.task,
                agent_type=routing["agent"],
                status="pending"
            )
        
        # Add subtasks if any
        for subtask in routing.get("subtasks", []):
            if subtask["agent"] not in state.agents:
                state.agents[subtask["agent"]] = AgentState(
                    task=subtask["task"],
                    agent_type=subtask["agent"],
                    status="pending"
                )
        
        # Add routing decision to messages
        state.messages.append({
            "role": "supervisor",
            "content": f"Routing task to {routing['agent']}: {routing['reason']}"
        })
        
        return state
    
    async def _build_manager_node(
        self,
        state: WorkflowState,
        **kwargs
    ) -> WorkflowState:
        """Handle build manager node logic.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        agent_state = state.agents[state.current_agent]
        
        # Execute task
        result = await build_manager.handle_task(agent_state.task)
        
        # Update state
        agent_state.status = result["status"]
        agent_state.result = result
        
        # Add result to messages
        state.messages.append({
            "role": "build_manager",
            "content": f"Build task completed: {result['status']}"
        })
        
        # Add artifacts if any
        if "artifacts" in result:
            state.artifacts["build"] = result["artifacts"]
        
        return state
    
    async def _log_analyzer_node(
        self,
        state: WorkflowState,
        **kwargs
    ) -> WorkflowState:
        """Handle log analyzer node logic.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        agent_state = state.agents[state.current_agent]
        
        # Execute task
        result = await log_analyzer.handle_task(agent_state.task)
        
        # Update state
        agent_state.status = result["status"]
        agent_state.result = result
        
        # Add result to messages
        state.messages.append({
            "role": "log_analyzer",
            "content": f"Log analysis completed: {result['status']}"
        })
        
        # Add artifacts if any
        if "analysis" in result:
            state.artifacts["logs"] = result["analysis"]
        
        return state
    
    async def _pipeline_manager_node(
        self,
        state: WorkflowState,
        **kwargs
    ) -> WorkflowState:
        """Handle pipeline manager node logic.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        agent_state = state.agents[state.current_agent]
        
        # Execute task
        result = await pipeline_manager.handle_task(agent_state.task)
        
        # Update state
        agent_state.status = result["status"]
        agent_state.result = result
        
        # Add result to messages
        state.messages.append({
            "role": "pipeline_manager",
            "content": f"Pipeline task completed: {result['status']}"
        })
        
        # Add artifacts if any
        if "pipeline" in result:
            state.artifacts["pipeline"] = result["pipeline"]
        
        return state
    
    async def _plugin_manager_node(
        self,
        state: WorkflowState,
        **kwargs
    ) -> WorkflowState:
        """Handle plugin manager node logic.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        agent_state = state.agents[state.current_agent]
        
        # Execute task
        result = await plugin_manager.handle_task(agent_state.task)
        
        # Update state
        agent_state.status = result["status"]
        agent_state.result = result
        
        # Add result to messages
        state.messages.append({
            "role": "plugin_manager",
            "content": f"Plugin task completed: {result['status']}"
        })
        
        # Add artifacts if any
        if "plugins" in result:
            state.artifacts["plugins"] = result["plugins"]
        
        return state
    
    def _should_route_to_build(self, state: WorkflowState) -> bool:
        """Check if task should be routed to build manager."""
        return state.current_agent == "build_manager"
    
    def _should_route_to_logs(self, state: WorkflowState) -> bool:
        """Check if task should be routed to log analyzer."""
        return state.current_agent == "log_analyzer"
    
    def _should_route_to_pipeline(self, state: WorkflowState) -> bool:
        """Check if task should be routed to pipeline manager."""
        return state.current_agent == "pipeline_manager"
    
    def _should_route_to_plugin(self, state: WorkflowState) -> bool:
        """Check if task should be routed to plugin manager."""
        return state.current_agent == "plugin_manager"
    
    async def _needs_coordination(self, state: WorkflowState) -> bool:
        """Check if workflow needs coordination."""
        # Get coordination decision
        response = await self.llm.agenerate([{
            "role": "user",
            "content": self.coordination_prompt.format(
                workflow_state=json.dumps(vars(state))
            )
        }])
        
        coordination = json.loads(response.generations[0].text)
        
        # Update state with coordination info
        if coordination["next_agent"] != "end":
            state.current_agent = coordination["next_agent"]
            state.messages.append({
                "role": "coordinator",
                "content": f"Coordinating: {coordination['reason']}"
            })
            
            # Execute coordination actions
            for action in coordination.get("coordination", []):
                if action["type"] == "share_artifact":
                    source = action["source"]
                    target = action["target"]
                    if source in state.artifacts:
                        if target not in state.agents:
                            state.agents[target] = AgentState(
                                task=f"Process {source} artifact",
                                agent_type=target,
                                status="pending"
                            )
                        state.agents[target].next_steps.append(
                            f"Process {source} artifact"
                        )
        
        return coordination["next_agent"] != "end"
    
    def _is_workflow_complete(self, state: WorkflowState) -> bool:
        """Check if workflow is complete."""
        return all(
            agent.status in ["success", "error"]
            for agent in state.agents.values()
        )
    
    @handle_errors()
    async def execute_workflow(self, task: str) -> Dict[str, Any]:
        """Execute a workflow for a task.
        
        Args:
            task: Task description
            
        Returns:
            Workflow results
        """
        # Initialize workflow state
        state = WorkflowState(
            task=task,
            current_agent="supervisor",
            agents={},
            messages=[],
            artifacts={}
        )
        
        # Run workflow
        final_state = await self.graph.arun(state)
        
        return {
            "status": "success",
            "task": task,
            "agents": {
                name: vars(agent)
                for name, agent in final_state.agents.items()
            },
            "messages": final_state.messages,
            "artifacts": final_state.artifacts
        }

# Global instance
workflow_manager = WorkflowManager()