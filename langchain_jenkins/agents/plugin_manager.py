"""Plugin manager agent for handling Jenkins plugins."""
from typing import Dict, Any, List
from langchain.tools import Tool
from .base_agent import BaseAgent
from ..tools.plugin_tools import PluginTools

class PluginManagerAgent(BaseAgent):
    """Agent for managing Jenkins plugins."""
    
    def __init__(self):
        """Initialize plugin manager agent with required tools."""
        self.plugin_tools = PluginTools()
        
        tools = [
            Tool(
                name="GetInstalledPlugins",
                func=self.plugin_tools.get_installed_plugins,
                description="Get information about installed Jenkins plugins"
            ),
            Tool(
                name="GetAvailablePlugins",
                func=self.plugin_tools.get_available_plugins,
                description="Get information about available Jenkins plugins"
            ),
            Tool(
                name="InstallPlugin",
                func=self.plugin_tools.install_plugin,
                description="Install a Jenkins plugin"
            ),
            Tool(
                name="UninstallPlugin",
                func=self.plugin_tools.uninstall_plugin,
                description="Uninstall a Jenkins plugin"
            ),
            Tool(
                name="CheckUpdates",
                func=self.plugin_tools.check_updates,
                description="Check for plugin updates"
            ),
            Tool(
                name="UpdateAllPlugins",
                func=self.plugin_tools.update_all_plugins,
                description="Update all plugins that have updates available"
            ),
            Tool(
                name="GetPluginDependencies",
                func=self.plugin_tools.get_plugin_dependencies,
                description="Get dependencies for a plugin"
            ),
            Tool(
                name="AnalyzePluginHealth",
                func=self.plugin_tools.analyze_plugin_health,
                description="Analyze the health of installed plugins"
            )
        ]
        
        super().__init__(tools)
    
    async def handle_task(self, task: str) -> Dict[str, Any]:
        """Handle plugin-related tasks.
        
        Args:
            task: Description of the plugin task to perform
            
        Returns:
            Result of the task execution
        """
        task_lower = task.lower()
        
        if "install" in task_lower:
            return await self._handle_plugin_installation(task)
        elif "uninstall" in task_lower or "remove" in task_lower:
            return await self._handle_plugin_uninstallation(task)
        elif "update" in task_lower:
            return await self._handle_plugin_updates(task)
        elif "health" in task_lower or "analyze" in task_lower:
            return await self._handle_plugin_health(task)
        elif "list" in task_lower or "show" in task_lower:
            return await self._handle_plugin_list(task)
        else:
            return {
                "status": "error",
                "error": "Unsupported plugin task",
                "task": task
            }
    
    async def _handle_plugin_installation(self, task: str) -> Dict[str, Any]:
        """Handle plugin installation tasks.
        
        Args:
            task: Plugin installation task description
            
        Returns:
            Installation results
        """
        # Extract plugin name from task
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
        
        try:
            # Check dependencies first
            deps = await self.plugin_tools.get_plugin_dependencies(plugin_name)
            
            # Install the plugin
            result = await self.plugin_tools.install_plugin(plugin_name)
            
            return {
                "status": "success",
                "plugin": plugin_name,
                "installation_status": result,
                "dependencies": deps.get("dependencies", [])
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "plugin": plugin_name
            }
    
    async def _handle_plugin_uninstallation(self, task: str) -> Dict[str, Any]:
        """Handle plugin uninstallation tasks.
        
        Args:
            task: Plugin uninstallation task description
            
        Returns:
            Uninstallation results
        """
        # Extract plugin name from task
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
        
        try:
            # Check dependencies first
            deps = await self.plugin_tools.get_plugin_dependencies(plugin_name)
            
            if deps.get("dependencies"):
                return {
                    "status": "error",
                    "error": "Plugin has dependencies",
                    "plugin": plugin_name,
                    "dependencies": deps["dependencies"]
                }
            
            # Uninstall the plugin
            result = await self.plugin_tools.uninstall_plugin(plugin_name)
            
            return {
                "status": "success",
                "plugin": plugin_name,
                "uninstallation_status": result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "plugin": plugin_name
            }
    
    async def _handle_plugin_updates(self, task: str) -> Dict[str, Any]:
        """Handle plugin update tasks.
        
        Args:
            task: Plugin update task description
            
        Returns:
            Update results
        """
        try:
            if "all" in task.lower():
                # Update all plugins
                updates = await self.plugin_tools.check_updates()
                if updates["updates_available"] > 0:
                    result = await self.plugin_tools.update_all_plugins()
                    return {
                        "status": "success",
                        "updates_available": updates["updates_available"],
                        "update_status": result
                    }
                else:
                    return {
                        "status": "success",
                        "message": "No updates available"
                    }
            else:
                # Just check for updates
                updates = await self.plugin_tools.check_updates()
                return {
                    "status": "success",
                    "updates": updates
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _handle_plugin_health(self, task: str) -> Dict[str, Any]:
        """Handle plugin health analysis tasks.
        
        Args:
            task: Plugin health task description
            
        Returns:
            Health analysis results
        """
        try:
            analysis = await self.plugin_tools.analyze_plugin_health()
            return {
                "status": "success",
                "health_analysis": analysis
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _handle_plugin_list(self, task: str) -> Dict[str, Any]:
        """Handle plugin listing tasks.
        
        Args:
            task: Plugin list task description
            
        Returns:
            Plugin list results
        """
        try:
            if "available" in task.lower():
                plugins = await self.plugin_tools.get_available_plugins()
                return {
                    "status": "success",
                    "available_plugins": plugins
                }
            else:
                plugins = await self.plugin_tools.get_installed_plugins()
                return {
                    "status": "success",
                    "installed_plugins": plugins
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }