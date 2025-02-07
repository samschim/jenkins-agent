"""Enhanced Pipeline Manager Agent with advanced features.

Features:
- Pipeline configuration management
- Jenkinsfile editing
- Git integration
- Dependency management
- Automated validation
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import asyncio
import re
import json
import base64
from langchain.tools import Tool
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from .base_agent import BaseAgent
from ..config.config import config
from ..utils.cache import cache
from ..utils.error_handler import handle_errors

@dataclass
class PipelineStage:
    """Pipeline stage information."""
    name: str
    steps: List[Dict[str, Any]]
    conditions: List[str]
    environment: Dict[str, str]
    agents: List[str]

@dataclass
class PipelineConfig:
    """Pipeline configuration."""
    name: str
    stages: List[PipelineStage]
    triggers: List[str]
    environment: Dict[str, str]
    parameters: List[Dict[str, Any]]
    post_actions: Dict[str, List[str]]

class EnhancedPipelineManager(BaseAgent):
    """Enhanced agent for managing Jenkins pipelines."""
    
    def __init__(self):
        """Initialize pipeline manager with enhanced capabilities."""
        self.llm = ChatOpenAI(
            model=config.llm.model,
            temperature=0.1
        )
        
        # Create validation chain
        self.validation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at validating Jenkins pipelines.
Analyze this pipeline configuration and identify any issues.

Format your response as JSON with these keys:
- valid: boolean indicating if the pipeline is valid
- issues: list of identified issues
- suggestions: list of improvement suggestions
- security_concerns: list of security issues
- best_practices: list of best practice recommendations"""),
            ("human", "{pipeline_config}")
        ])
        
        tools = [
            Tool(
                name="GetPipeline",
                func=self._get_pipeline,
                description="Get pipeline configuration"
            ),
            Tool(
                name="UpdatePipeline",
                func=self._update_pipeline,
                description="Update pipeline configuration"
            ),
            Tool(
                name="ValidatePipeline",
                func=self._validate_pipeline,
                description="Validate pipeline configuration"
            ),
            Tool(
                name="GetJenkinsfile",
                func=self._get_jenkinsfile,
                description="Get Jenkinsfile content"
            ),
            Tool(
                name="UpdateJenkinsfile",
                func=self._update_jenkinsfile,
                description="Update Jenkinsfile content"
            ),
            Tool(
                name="ManageDependencies",
                func=self._manage_dependencies,
                description="Manage pipeline dependencies"
            ),
            Tool(
                name="SyncWithGit",
                func=self._sync_with_git,
                description="Sync pipeline with Git repository"
            )
        ]
        
        super().__init__(tools)
    
    @handle_errors()
    async def _get_pipeline(
        self,
        pipeline_name: str
    ) -> PipelineConfig:
        """Get pipeline configuration.
        
        Args:
            pipeline_name: Name of the pipeline
            
        Returns:
            Pipeline configuration
        """
        # Get pipeline config from Jenkins
        config_xml = await self.jenkins.get(
            f"/job/{pipeline_name}/config.xml"
        )
        
        # Parse pipeline configuration
        stages = []
        for stage_xml in re.finditer(r"<stage>(.*?)</stage>", config_xml):
            stage_data = stage_xml.group(1)
            stages.append(PipelineStage(
                name=re.search(r"<name>(.*?)</name>", stage_data).group(1),
                steps=json.loads(re.search(r"<steps>(.*?)</steps>", stage_data).group(1)),
                conditions=json.loads(re.search(r"<conditions>(.*?)</conditions>", stage_data).group(1)),
                environment=json.loads(re.search(r"<environment>(.*?)</environment>", stage_data).group(1)),
                agents=json.loads(re.search(r"<agents>(.*?)</agents>", stage_data).group(1))
            ))
        
        return PipelineConfig(
            name=pipeline_name,
            stages=stages,
            triggers=json.loads(re.search(r"<triggers>(.*?)</triggers>", config_xml).group(1)),
            environment=json.loads(re.search(r"<environment>(.*?)</environment>", config_xml).group(1)),
            parameters=json.loads(re.search(r"<parameters>(.*?)</parameters>", config_xml).group(1)),
            post_actions=json.loads(re.search(r"<postActions>(.*?)</postActions>", config_xml).group(1))
        )
    
    @handle_errors()
    async def _update_pipeline(
        self,
        pipeline: PipelineConfig
    ) -> Dict[str, Any]:
        """Update pipeline configuration.
        
        Args:
            pipeline: Pipeline configuration
            
        Returns:
            Update status
        """
        # Validate pipeline first
        validation = await self._validate_pipeline(pipeline)
        if not validation["valid"]:
            return {
                "status": "error",
                "error": "Invalid pipeline configuration",
                "validation": validation
            }
        
        # Convert pipeline to XML
        config_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<flow-definition>
    <actions/>
    <description>{pipeline.name} Pipeline</description>
    <keepDependencies>false</keepDependencies>
    <properties>
        <parameters>{json.dumps(pipeline.parameters)}</parameters>
    </properties>
    <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition">
        <script>
            pipeline {{
                agent any
                environment {json.dumps(pipeline.environment)}
                triggers {json.dumps(pipeline.triggers)}
                stages {{
                    {self._stages_to_xml(pipeline.stages)}
                }}
                post {{
                    {self._post_actions_to_xml(pipeline.post_actions)}
                }}
            }}
        </script>
    </definition>
</flow-definition>"""
        
        # Update pipeline in Jenkins
        await self.jenkins.post(
            f"/job/{pipeline.name}/config.xml",
            config_xml
        )
        
        return {
            "status": "updated",
            "pipeline": pipeline.name
        }
    
    def _stages_to_xml(self, stages: List[PipelineStage]) -> str:
        """Convert stages to XML format."""
        xml = ""
        for stage in stages:
            xml += f"""
                stage('{stage.name}') {{
                    agent {{ label '{' || '.join(stage.agents)}' }}
                    when {{ {' && '.join(stage.conditions)} }}
                    environment {json.dumps(stage.environment)}
                    steps {{
                        {self._steps_to_groovy(stage.steps)}
                    }}
                }}"""
        return xml
    
    def _steps_to_groovy(self, steps: List[Dict[str, Any]]) -> str:
        """Convert steps to Groovy script."""
        groovy = ""
        for step in steps:
            if step["type"] == "sh":
                groovy += f"sh '{step['command']}'\n"
            elif step["type"] == "script":
                groovy += f"script {{\n{step['script']}\n}}\n"
            elif step["type"] == "dir":
                groovy += f"dir('{step['path']}') {{\n{self._steps_to_groovy(step['steps'])}\n}}\n"
        return groovy
    
    def _post_actions_to_xml(self, actions: Dict[str, List[str]]) -> str:
        """Convert post actions to XML format."""
        xml = ""
        for condition, steps in actions.items():
            xml += f"""
                {condition} {{
                    {' '.join(steps)}
                }}"""
        return xml
    
    @handle_errors()
    async def _validate_pipeline(
        self,
        pipeline: PipelineConfig
    ) -> Dict[str, Any]:
        """Validate pipeline configuration.
        
        Args:
            pipeline: Pipeline configuration
            
        Returns:
            Validation results
        """
        # Convert pipeline to string for LLM
        pipeline_str = json.dumps(vars(pipeline), indent=2)
        
        # Get LLM validation
        response = await self.llm.agenerate([{
            "role": "user",
            "content": self.validation_prompt.format(
                pipeline_config=pipeline_str
            )
        }])
        
        return json.loads(response.generations[0].text)
    
    @handle_errors()
    async def _get_jenkinsfile(
        self,
        pipeline_name: str,
        branch: str = "main"
    ) -> str:
        """Get Jenkinsfile content from Git.
        
        Args:
            pipeline_name: Name of the pipeline
            branch: Git branch name
            
        Returns:
            Jenkinsfile content
        """
        # Get repository info
        repo_info = await self.jenkins.get(
            f"/job/{pipeline_name}/config.xml"
        )
        repo_url = re.search(r"<remote>(.*?)</remote>", repo_info).group(1)
        
        # Get Jenkinsfile from GitHub
        headers = {
            "Authorization": f"token {config.github.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        async with httpx.AsyncClient() as client:
            # Get repository details
            repo_parts = repo_url.split("/")[-2:]
            repo_api = f"https://api.github.com/repos/{repo_parts[0]}/{repo_parts[1]}"
            
            # Get Jenkinsfile content
            response = await client.get(
                f"{repo_api}/contents/Jenkinsfile",
                headers=headers,
                params={"ref": branch}
            )
            
            if response.status_code == 200:
                content = response.json()["content"]
                return base64.b64decode(content).decode("utf-8")
            else:
                raise ValueError(f"Failed to get Jenkinsfile: {response.text}")
    
    @handle_errors()
    async def _update_jenkinsfile(
        self,
        pipeline_name: str,
        content: str,
        message: str = "Update Jenkinsfile",
        branch: str = "main"
    ) -> Dict[str, Any]:
        """Update Jenkinsfile in Git.
        
        Args:
            pipeline_name: Name of the pipeline
            content: New Jenkinsfile content
            message: Commit message
            branch: Git branch name
            
        Returns:
            Update status
        """
        # Get repository info
        repo_info = await self.jenkins.get(
            f"/job/{pipeline_name}/config.xml"
        )
        repo_url = re.search(r"<remote>(.*?)</remote>", repo_info).group(1)
        
        # Update Jenkinsfile in GitHub
        headers = {
            "Authorization": f"token {config.github.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        async with httpx.AsyncClient() as client:
            # Get repository details
            repo_parts = repo_url.split("/")[-2:]
            repo_api = f"https://api.github.com/repos/{repo_parts[0]}/{repo_parts[1]}"
            
            # Get current file SHA
            response = await client.get(
                f"{repo_api}/contents/Jenkinsfile",
                headers=headers,
                params={"ref": branch}
            )
            
            if response.status_code == 200:
                current = response.json()
                
                # Update file
                update_data = {
                    "message": message,
                    "content": base64.b64encode(content.encode()).decode(),
                    "sha": current["sha"],
                    "branch": branch
                }
                
                response = await client.put(
                    f"{repo_api}/contents/Jenkinsfile",
                    headers=headers,
                    json=update_data
                )
                
                if response.status_code == 200:
                    return {
                        "status": "updated",
                        "commit": response.json()["commit"]["sha"]
                    }
                else:
                    raise ValueError(f"Failed to update Jenkinsfile: {response.text}")
            else:
                raise ValueError(f"Failed to get current Jenkinsfile: {response.text}")
    
    @handle_errors()
    async def _manage_dependencies(
        self,
        pipeline_name: str,
        upstream: Optional[List[str]] = None,
        downstream: Optional[List[str]] = None,
        triggers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Manage pipeline dependencies.
        
        Args:
            pipeline_name: Name of the pipeline
            upstream: Upstream pipeline names
            downstream: Downstream pipeline names
            triggers: Pipeline triggers
            
        Returns:
            Update status
        """
        # Get current configuration
        pipeline = await self._get_pipeline(pipeline_name)
        
        # Update dependencies
        if upstream:
            pipeline.triggers.extend([
                f"upstream(upstreamProjects: '{','.join(upstream)}', threshold: hudson.model.Result.SUCCESS)"
            ])
        
        if downstream:
            pipeline.post_actions["success"] = pipeline.post_actions.get("success", []) + [
                f"build(job: '{job}'))" for job in downstream
            ]
        
        if triggers:
            pipeline.triggers.extend(triggers)
        
        # Update pipeline
        return await self._update_pipeline(pipeline)
    
    @handle_errors()
    async def _sync_with_git(
        self,
        pipeline_name: str,
        branch: str = "main"
    ) -> Dict[str, Any]:
        """Sync pipeline with Git repository.
        
        Args:
            pipeline_name: Name of the pipeline
            branch: Git branch name
            
        Returns:
            Sync status
        """
        # Get Jenkinsfile from Git
        jenkinsfile = await self._get_jenkinsfile(pipeline_name, branch)
        
        # Parse Jenkinsfile into pipeline config
        config = self._parse_jenkinsfile(jenkinsfile)
        
        # Update pipeline in Jenkins
        return await self._update_pipeline(config)
    
    def _parse_jenkinsfile(self, jenkinsfile: str) -> PipelineConfig:
        """Parse Jenkinsfile into pipeline configuration."""
        # Use LLM to help parse complex Jenkinsfile
        response = self.llm.generate([{
            "role": "user",
            "content": f"""
Parse this Jenkinsfile and extract the pipeline configuration:

{jenkinsfile}

Format your response as JSON matching this structure:
{{
    "name": "pipeline name",
    "stages": [
        {{
            "name": "stage name",
            "steps": [{{...}}],
            "conditions": ["condition1"],
            "environment": {{"key": "value"}},
            "agents": ["agent1"]
        }}
    ],
    "triggers": ["trigger1"],
    "environment": {{"key": "value"}},
    "parameters": [{{"name": "param1", "type": "string"}}],
    "post_actions": {{"success": ["action1"]}}
}}
"""
        }])
        
        config_dict = json.loads(response.generations[0].text)
        return PipelineConfig(**config_dict)
    
    async def handle_task(self, task: str) -> Dict[str, Any]:
        """Handle pipeline management tasks.
        
        Args:
            task: Description of the pipeline task
            
        Returns:
            Task result
        """
        task_lower = task.lower()
        
        if "get" in task_lower and "pipeline" in task_lower:
            return await self._handle_get_pipeline(task)
        elif "update" in task_lower and "pipeline" in task_lower:
            return await self._handle_update_pipeline(task)
        elif "validate" in task_lower:
            return await self._handle_validate_pipeline(task)
        elif "jenkinsfile" in task_lower:
            return await self._handle_jenkinsfile_task(task)
        elif "dependency" in task_lower or "dependencies" in task_lower:
            return await self._handle_dependencies(task)
        elif "sync" in task_lower or "git" in task_lower:
            return await self._handle_git_sync(task)
        else:
            return {
                "status": "error",
                "error": "Unsupported pipeline task",
                "task": task
            }
    
    async def _handle_get_pipeline(self, task: str) -> Dict[str, Any]:
        """Handle get pipeline requests."""
        # Extract pipeline name
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
        
        pipeline = await self._get_pipeline(pipeline_name)
        return {
            "status": "success",
            "pipeline": vars(pipeline)
        }
    
    async def _handle_update_pipeline(self, task: str) -> Dict[str, Any]:
        """Handle update pipeline requests."""
        # Extract pipeline configuration
        if "config" not in task.lower():
            return {
                "status": "error",
                "error": "No pipeline configuration provided",
                "task": task
            }
        
        config_text = task[task.lower().index("config") + 6:].strip()
        try:
            config_dict = json.loads(config_text)
            pipeline = PipelineConfig(**config_dict)
        except Exception as e:
            return {
                "status": "error",
                "error": f"Invalid pipeline configuration: {str(e)}",
                "task": task
            }
        
        return await self._update_pipeline(pipeline)
    
    async def _handle_validate_pipeline(self, task: str) -> Dict[str, Any]:
        """Handle pipeline validation requests."""
        # Extract pipeline configuration
        if "config" not in task.lower():
            return {
                "status": "error",
                "error": "No pipeline configuration provided",
                "task": task
            }
        
        config_text = task[task.lower().index("config") + 6:].strip()
        try:
            config_dict = json.loads(config_text)
            pipeline = PipelineConfig(**config_dict)
        except Exception as e:
            return {
                "status": "error",
                "error": f"Invalid pipeline configuration: {str(e)}",
                "task": task
            }
        
        return await self._validate_pipeline(pipeline)
    
    async def _handle_jenkinsfile_task(self, task: str) -> Dict[str, Any]:
        """Handle Jenkinsfile tasks."""
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
        
        if "get" in task.lower():
            jenkinsfile = await self._get_jenkinsfile(pipeline_name)
            return {
                "status": "success",
                "jenkinsfile": jenkinsfile
            }
        elif "update" in task.lower():
            if "content" not in task.lower():
                return {
                    "status": "error",
                    "error": "No Jenkinsfile content provided",
                    "task": task
                }
            
            content = task[task.lower().index("content") + 7:].strip()
            return await self._update_jenkinsfile(pipeline_name, content)
    
    async def _handle_dependencies(self, task: str) -> Dict[str, Any]:
        """Handle dependency management tasks."""
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
        
        # Extract dependencies
        upstream = []
        downstream = []
        triggers = []
        
        if "upstream" in task.lower():
            idx = words.index("upstream")
            while idx + 1 < len(words) and "downstream" not in words[idx + 1].lower():
                upstream.append(words[idx + 1])
                idx += 1
        
        if "downstream" in task.lower():
            idx = words.index("downstream")
            while idx + 1 < len(words) and "trigger" not in words[idx + 1].lower():
                downstream.append(words[idx + 1])
                idx += 1
        
        if "trigger" in task.lower():
            idx = words.index("trigger")
            while idx + 1 < len(words):
                triggers.append(words[idx + 1])
                idx += 1
        
        return await self._manage_dependencies(
            pipeline_name,
            upstream or None,
            downstream or None,
            triggers or None
        )
    
    async def _handle_git_sync(self, task: str) -> Dict[str, Any]:
        """Handle Git sync tasks."""
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
        
        # Extract branch if specified
        branch = "main"
        if "branch" in task.lower():
            idx = words.index("branch")
            if idx + 1 < len(words):
                branch = words[idx + 1]
        
        return await self._sync_with_git(pipeline_name, branch)

# Global instance
pipeline_manager = EnhancedPipelineManager()