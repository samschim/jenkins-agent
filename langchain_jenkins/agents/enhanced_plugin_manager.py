"""Enhanced Plugin Manager Agent with advanced features.

Features:
- Plugin installation and updates
- Dependency resolution
- Security scanning
- Compatibility checking
- Update scheduling
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio
import json
import httpx
from langchain.tools import Tool
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from .base_agent import BaseAgent
from ..config.config import config
from ..utils.cache import cache
from ..utils.error_handler import handle_errors

@dataclass
class PluginInfo:
    """Plugin information."""
    name: str
    version: str
    latest_version: Optional[str]
    dependencies: List[str]
    security_warnings: List[str]
    enabled: bool
    pinned: bool
    url: str

@dataclass
class SecurityIssue:
    """Security issue information."""
    plugin: str
    severity: str
    description: str
    cve: Optional[str]
    fix_version: Optional[str]
    mitigation: str

class EnhancedPluginManager(BaseAgent):
    """Enhanced agent for managing Jenkins plugins."""
    
    def __init__(self):
        """Initialize plugin manager with enhanced capabilities."""
        self.llm = ChatOpenAI(
            model=config.llm.model,
            temperature=0.1
        )
        
        # Create security analysis chain
        self.security_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at analyzing Jenkins plugin security.
Analyze these plugins and identify security issues.

Format your response as JSON with these keys:
- issues: list of security issues with severity and description
- recommendations: list of security recommendations
- urgent_updates: list of plugins requiring immediate updates
- best_practices: list of security best practices"""),
            ("human", "{plugin_data}")
        ])
        
        tools = [
            Tool(
                name="ListPlugins",
                func=self._list_plugins,
                description="List installed Jenkins plugins"
            ),
            Tool(
                name="InstallPlugin",
                func=self._install_plugin,
                description="Install a Jenkins plugin"
            ),
            Tool(
                name="UpdatePlugin",
                func=self._update_plugin,
                description="Update a Jenkins plugin"
            ),
            Tool(
                name="UninstallPlugin",
                func=self._uninstall_plugin,
                description="Uninstall a Jenkins plugin"
            ),
            Tool(
                name="CheckUpdates",
                func=self._check_updates,
                description="Check for plugin updates"
            ),
            Tool(
                name="ScanSecurity",
                func=self._scan_security,
                description="Scan plugins for security issues"
            ),
            Tool(
                name="ResolveDependencies",
                func=self._resolve_dependencies,
                description="Resolve plugin dependencies"
            ),
            Tool(
                name="CheckCompatibility",
                func=self._check_compatibility,
                description="Check plugin compatibility"
            )
        ]
        
        super().__init__(tools)
    
    @handle_errors()
    async def _list_plugins(
        self,
        include_disabled: bool = False
    ) -> List[PluginInfo]:
        """List installed plugins.
        
        Args:
            include_disabled: Whether to include disabled plugins
            
        Returns:
            List of plugin information
        """
        response = await self.jenkins.get(
            "/pluginManager/api/json?depth=2"
        )
        
        plugins = []
        for plugin in response.get("plugins", []):
            if not include_disabled and not plugin.get("enabled", True):
                continue
            
            plugins.append(PluginInfo(
                name=plugin["shortName"],
                version=plugin["version"],
                latest_version=plugin.get("latestVersion"),
                dependencies=[d["shortName"] for d in plugin.get("dependencies", [])],
                security_warnings=plugin.get("securityWarnings", []),
                enabled=plugin.get("enabled", True),
                pinned=plugin.get("pinned", False),
                url=plugin.get("url", "")
            ))
        
        return plugins
    
    @handle_errors()
    async def _install_plugin(
        self,
        name: str,
        version: Optional[str] = None,
        with_dependencies: bool = True
    ) -> Dict[str, Any]:
        """Install a Jenkins plugin.
        
        Args:
            name: Plugin name
            version: Optional specific version
            with_dependencies: Whether to install dependencies
            
        Returns:
            Installation status
        """
        # Check if plugin exists
        if version:
            url = f"https://updates.jenkins.io/download/plugins/{name}/{version}/{name}.hpi"
        else:
            url = f"https://updates.jenkins.io/latest/{name}.hpi"
        
        # Get dependencies if needed
        dependencies = []
        if with_dependencies:
            plugin_info = await self._get_plugin_info(name)
            dependencies = plugin_info.get("dependencies", [])
            
            # Install dependencies first
            for dep in dependencies:
                await self._install_plugin(
                    dep["name"],
                    dep.get("version"),
                    with_dependencies=True
                )
        
        # Install plugin
        response = await self.jenkins.post(
            "/pluginManager/installNecessaryPlugins",
            {"plugin.%s.%s" % (name, version or "latest"): "on"}
        )
        
        return {
            "status": "installed",
            "plugin": name,
            "version": version or "latest",
            "dependencies": dependencies
        }
    
    @handle_errors()
    async def _update_plugin(
        self,
        name: str,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update a Jenkins plugin.
        
        Args:
            name: Plugin name
            version: Optional target version
            
        Returns:
            Update status
        """
        # Check current version
        plugins = await self._list_plugins()
        current = next((p for p in plugins if p.name == name), None)
        if not current:
            return {
                "status": "error",
                "error": f"Plugin {name} not installed"
            }
        
        # Check if update needed
        if version and version == current.version:
            return {
                "status": "up-to-date",
                "plugin": name,
                "version": version
            }
        
        # Update plugin
        response = await self.jenkins.post(
            "/pluginManager/install",
            {"plugin.%s.%s" % (name, version or "latest"): "on"}
        )
        
        return {
            "status": "updated",
            "plugin": name,
            "from_version": current.version,
            "to_version": version or "latest"
        }
    
    @handle_errors()
    async def _uninstall_plugin(
        self,
        name: str,
        check_dependencies: bool = True
    ) -> Dict[str, Any]:
        """Uninstall a Jenkins plugin.
        
        Args:
            name: Plugin name
            check_dependencies: Whether to check for dependent plugins
            
        Returns:
            Uninstall status
        """
        # Check dependencies
        if check_dependencies:
            plugins = await self._list_plugins()
            dependents = []
            for plugin in plugins:
                if name in plugin.dependencies:
                    dependents.append(plugin.name)
            
            if dependents:
                return {
                    "status": "error",
                    "error": "Plugin has dependents",
                    "plugin": name,
                    "dependents": dependents
                }
        
        # Uninstall plugin
        response = await self.jenkins.post(
            f"/pluginManager/plugin/{name}/doUninstall"
        )
        
        return {
            "status": "uninstalled",
            "plugin": name
        }
    
    @handle_errors()
    async def _check_updates(
        self,
        include_security: bool = True
    ) -> Dict[str, Any]:
        """Check for plugin updates.
        
        Args:
            include_security: Whether to include security updates
            
        Returns:
            Update information
        """
        # Get update center data
        response = await self.jenkins.get(
            "/updateCenter/api/json?depth=2"
        )
        
        updates = []
        security_updates = []
        
        for site in response.get("sites", []):
            for update in site.get("updates", []):
                plugin_name = update["name"]
                current_version = update.get("currentVersion")
                new_version = update["version"]
                
                if update.get("security"):
                    security_updates.append({
                        "plugin": plugin_name,
                        "current_version": current_version,
                        "new_version": new_version,
                        "security_warnings": update.get("securityWarnings", [])
                    })
                else:
                    updates.append({
                        "plugin": plugin_name,
                        "current_version": current_version,
                        "new_version": new_version
                    })
        
        return {
            "status": "success",
            "updates": updates,
            "security_updates": security_updates if include_security else []
        }
    
    @handle_errors()
    async def _scan_security(
        self,
        plugins: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Scan plugins for security issues.
        
        Args:
            plugins: Optional list of plugins to scan
            
        Returns:
            Security scan results
        """
        # Get plugin data
        installed = await self._list_plugins()
        if plugins:
            installed = [p for p in installed if p.name in plugins]
        
        # Get security warnings
        response = await self.jenkins.get(
            "/securityWarnings/api/json"
        )
        
        warnings = []
        for warning in response.get("warnings", []):
            plugin = warning["plugin"]
            if plugins and plugin not in plugins:
                continue
            
            warnings.append(SecurityIssue(
                plugin=plugin,
                severity=warning["severity"],
                description=warning["message"],
                cve=warning.get("cve"),
                fix_version=warning.get("fixVersion"),
                mitigation=warning.get("mitigation", "Update to latest version")
            ))
        
        # Use LLM for deeper analysis
        analysis = await self.llm.agenerate([{
            "role": "user",
            "content": self.security_prompt.format(
                plugin_data=json.dumps([vars(p) for p in installed])
            )
        }])
        
        result = json.loads(analysis.generations[0].text)
        
        return {
            "status": "success",
            "warnings": [vars(w) for w in warnings],
            "analysis": result
        }
    
    @handle_errors()
    async def _resolve_dependencies(
        self,
        plugins: List[str]
    ) -> Dict[str, Any]:
        """Resolve plugin dependencies.
        
        Args:
            plugins: List of plugin names
            
        Returns:
            Dependency resolution results
        """
        # Get plugin information
        dependencies = {}
        for plugin in plugins:
            info = await self._get_plugin_info(plugin)
            dependencies[plugin] = {
                "required": info.get("dependencies", []),
                "optional": info.get("optionalDependencies", [])
            }
        
        # Build dependency graph
        graph = {}
        for plugin, deps in dependencies.items():
            graph[plugin] = {
                "required": [d["name"] for d in deps["required"]],
                "optional": [d["name"] for d in deps["optional"]]
            }
        
        # Check for cycles
        visited = set()
        path = []
        
        def has_cycle(node):
            if node in path:
                return True
            if node in visited:
                return False
            visited.add(node)
            path.append(node)
            for dep in graph[node]["required"]:
                if dep in graph and has_cycle(dep):
                    return True
            path.pop()
            return False
        
        cycles = []
        for plugin in plugins:
            if has_cycle(plugin):
                cycles.append(path[:])
        
        # Get installation order
        order = []
        visited = set()
        
        def visit(node):
            if node in visited:
                return
            visited.add(node)
            if node in graph:
                for dep in graph[node]["required"]:
                    visit(dep)
            order.append(node)
        
        for plugin in plugins:
            visit(plugin)
        
        return {
            "status": "success",
            "dependencies": dependencies,
            "cycles": cycles,
            "install_order": order
        }
    
    @handle_errors()
    async def _check_compatibility(
        self,
        plugins: List[str],
        jenkins_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check plugin compatibility.
        
        Args:
            plugins: List of plugin names
            jenkins_version: Optional Jenkins version
            
        Returns:
            Compatibility check results
        """
        if not jenkins_version:
            # Get current Jenkins version
            response = await self.jenkins.get("/api/json")
            jenkins_version = response["version"]
        
        compatibility = {}
        for plugin in plugins:
            info = await self._get_plugin_info(plugin)
            compatibility[plugin] = {
                "compatible": self._check_version_compatibility(
                    jenkins_version,
                    info.get("requiredCore", "1.0")
                ),
                "required_core": info.get("requiredCore"),
                "java_level": info.get("minimumJavaVersion")
            }
        
        return {
            "status": "success",
            "jenkins_version": jenkins_version,
            "compatibility": compatibility
        }
    
    async def _get_plugin_info(self, name: str) -> Dict[str, Any]:
        """Get plugin information from update center."""
        response = await self.jenkins.get(
            f"/pluginManager/plugin/{name}/api/json?depth=2"
        )
        return response
    
    def _check_version_compatibility(
        self,
        version: str,
        required: str
    ) -> bool:
        """Check version compatibility."""
        v1 = [int(x) for x in version.split(".")]
        v2 = [int(x) for x in required.split(".")]
        
        while len(v1) < len(v2):
            v1.append(0)
        while len(v2) < len(v1):
            v2.append(0)
        
        return v1 >= v2
    
    async def handle_task(self, task: str) -> Dict[str, Any]:
        """Handle plugin management tasks.
        
        Args:
            task: Description of the plugin task
            
        Returns:
            Task result
        """
        task_lower = task.lower()
        
        if "list" in task_lower and "plugin" in task_lower:
            return await self._handle_list_plugins(task)
        elif "install" in task_lower and "plugin" in task_lower:
            return await self._handle_install_plugin(task)
        elif "update" in task_lower and "plugin" in task_lower:
            return await self._handle_update_plugin(task)
        elif "uninstall" in task_lower and "plugin" in task_lower:
            return await self._handle_uninstall_plugin(task)
        elif "check" in task_lower and "update" in task_lower:
            return await self._handle_check_updates(task)
        elif "scan" in task_lower or "security" in task_lower:
            return await self._handle_security_scan(task)
        elif "dependency" in task_lower or "dependencies" in task_lower:
            return await self._handle_dependencies(task)
        elif "compatibility" in task_lower:
            return await self._handle_compatibility(task)
        else:
            return {
                "status": "error",
                "error": "Unsupported plugin task",
                "task": task
            }
    
    async def _handle_list_plugins(self, task: str) -> Dict[str, Any]:
        """Handle list plugins request."""
        include_disabled = "disabled" in task.lower()
        
        plugins = await self._list_plugins(include_disabled)
        return {
            "status": "success",
            "plugins": [vars(p) for p in plugins]
        }
    
    async def _handle_install_plugin(self, task: str) -> Dict[str, Any]:
        """Handle plugin installation request."""
        words = task.split()
        plugin_name = next(
            (word for word in words if "plugin" not in word.lower()),
            None
        )
        
        if not plugin_name:
            return {
                "status": "error",
                "error": "No plugin name specified",
                "task": task
            }
        
        # Extract version if specified
        version = None
        if "version" in task.lower():
            idx = words.index("version")
            if idx + 1 < len(words):
                version = words[idx + 1]
        
        # Check for dependency flag
        with_dependencies = "no-dependencies" not in task.lower()
        
        return await self._install_plugin(
            plugin_name,
            version,
            with_dependencies
        )
    
    async def _handle_update_plugin(self, task: str) -> Dict[str, Any]:
        """Handle plugin update request."""
        words = task.split()
        plugin_name = next(
            (word for word in words if "plugin" not in word.lower()),
            None
        )
        
        if not plugin_name:
            return {
                "status": "error",
                "error": "No plugin name specified",
                "task": task
            }
        
        # Extract version if specified
        version = None
        if "version" in task.lower():
            idx = words.index("version")
            if idx + 1 < len(words):
                version = words[idx + 1]
        
        return await self._update_plugin(plugin_name, version)
    
    async def _handle_uninstall_plugin(self, task: str) -> Dict[str, Any]:
        """Handle plugin uninstall request."""
        words = task.split()
        plugin_name = next(
            (word for word in words if "plugin" not in word.lower()),
            None
        )
        
        if not plugin_name:
            return {
                "status": "error",
                "error": "No plugin name specified",
                "task": task
            }
        
        # Check for force flag
        check_dependencies = "force" not in task.lower()
        
        return await self._uninstall_plugin(
            plugin_name,
            check_dependencies
        )
    
    async def _handle_check_updates(self, task: str) -> Dict[str, Any]:
        """Handle update check request."""
        include_security = "no-security" not in task.lower()
        
        return await self._check_updates(include_security)
    
    async def _handle_security_scan(self, task: str) -> Dict[str, Any]:
        """Handle security scan request."""
        # Extract plugin names if specified
        plugins = None
        if "plugin" in task.lower():
            words = task.split()
            idx = words.index("plugin")
            plugins = []
            while idx + 1 < len(words) and "scan" not in words[idx + 1].lower():
                plugins.append(words[idx + 1])
                idx += 1
        
        return await self._scan_security(plugins)
    
    async def _handle_dependencies(self, task: str) -> Dict[str, Any]:
        """Handle dependency resolution request."""
        if "resolve" not in task.lower():
            return {
                "status": "error",
                "error": "Invalid dependency task",
                "task": task
            }
        
        # Extract plugin names
        words = task.split()
        plugins = []
        for word in words:
            if "plugin" not in word.lower() and "resolve" not in word.lower():
                plugins.append(word)
        
        if not plugins:
            return {
                "status": "error",
                "error": "No plugins specified",
                "task": task
            }
        
        return await self._resolve_dependencies(plugins)
    
    async def _handle_compatibility(self, task: str) -> Dict[str, Any]:
        """Handle compatibility check request."""
        # Extract plugin names
        words = task.split()
        plugins = []
        for word in words:
            if "plugin" not in word.lower() and "check" not in word.lower():
                plugins.append(word)
        
        if not plugins:
            return {
                "status": "error",
                "error": "No plugins specified",
                "task": task
            }
        
        # Extract Jenkins version if specified
        jenkins_version = None
        if "version" in task.lower():
            idx = words.index("version")
            if idx + 1 < len(words):
                jenkins_version = words[idx + 1]
        
        return await self._check_compatibility(plugins, jenkins_version)

# Global instance
plugin_manager = EnhancedPluginManager()