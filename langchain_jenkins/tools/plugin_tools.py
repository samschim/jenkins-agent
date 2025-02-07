"""Plugin management tools for Jenkins."""
from typing import Dict, Any, List, Optional
from .jenkins_api import JenkinsAPI

class PluginTools:
    """Tools for managing Jenkins plugins."""
    
    def __init__(self):
        """Initialize plugin tools with Jenkins API client."""
        self.jenkins = JenkinsAPI()
    
    async def get_installed_plugins(self) -> Dict[str, Any]:
        """Get information about installed plugins.
        
        Returns:
            Dictionary containing installed plugins information
        """
        return await self.jenkins._request(
            "GET",
            "/pluginManager/api/json?depth=2"
        )
    
    async def get_available_plugins(self) -> Dict[str, Any]:
        """Get information about available plugins.
        
        Returns:
            Dictionary containing available plugins information
        """
        return await self.jenkins._request(
            "GET",
            "/pluginManager/available"
        )
    
    async def install_plugin(
        self,
        plugin_name: str,
        wait_for_install: bool = True
    ) -> Dict[str, Any]:
        """Install a Jenkins plugin.
        
        Args:
            plugin_name: Name of the plugin to install
            wait_for_install: Whether to wait for installation to complete
            
        Returns:
            Installation status information
        """
        # Start installation
        response = await self.jenkins._request(
            "POST",
            f"/pluginManager/install?plugin.{plugin_name}.default=on"
        )
        
        if not wait_for_install:
            return {"status": "installation_started", "plugin": plugin_name}
        
        # Wait for installation to complete
        max_attempts = 30
        attempt = 0
        while attempt < max_attempts:
            plugins = await self.get_installed_plugins()
            for plugin in plugins.get("plugins", []):
                if plugin["shortName"] == plugin_name:
                    if plugin.get("active", False):
                        return {
                            "status": "installed",
                            "plugin": plugin_name,
                            "version": plugin.get("version")
                        }
            attempt += 1
            await asyncio.sleep(2)
        
        return {
            "status": "timeout",
            "plugin": plugin_name,
            "message": "Installation did not complete in time"
        }
    
    async def uninstall_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Uninstall a Jenkins plugin.
        
        Args:
            plugin_name: Name of the plugin to uninstall
            
        Returns:
            Uninstallation status information
        """
        response = await self.jenkins._request(
            "POST",
            f"/pluginManager/plugin/{plugin_name}/uninstall"
        )
        return {
            "status": "uninstallation_started",
            "plugin": plugin_name
        }
    
    async def check_updates(self) -> Dict[str, Any]:
        """Check for plugin updates.
        
        Returns:
            Dictionary containing update information
        """
        # First check for updates
        await self.jenkins._request(
            "POST",
            "/pluginManager/checkUpdates"
        )
        
        # Get update information
        response = await self.jenkins._request(
            "GET",
            "/updateCenter/api/json?depth=1"
        )
        
        updates = []
        for job in response.get("jobs", []):
            if job.get("type") == "InstallationJob":
                updates.append({
                    "plugin": job.get("name"),
                    "version": job.get("version"),
                    "status": job.get("status")
                })
        
        return {
            "status": "success",
            "updates_available": len(updates),
            "updates": updates
        }
    
    async def update_all_plugins(self) -> Dict[str, Any]:
        """Update all plugins that have updates available.
        
        Returns:
            Update status information
        """
        # Start the update process
        response = await self.jenkins._request(
            "POST",
            "/pluginManager/installNecessaryPlugins"
        )
        
        return {
            "status": "updates_started",
            "message": "Plugin updates have been initiated"
        }
    
    async def get_plugin_dependencies(
        self,
        plugin_name: str
    ) -> Dict[str, Any]:
        """Get dependencies for a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Dictionary containing dependency information
        """
        plugins = await self.get_installed_plugins()
        
        for plugin in plugins.get("plugins", []):
            if plugin["shortName"] == plugin_name:
                return {
                    "plugin": plugin_name,
                    "dependencies": plugin.get("dependencies", []),
                    "optional_dependencies": plugin.get("optionalDependencies", [])
                }
        
        return {
            "status": "error",
            "message": f"Plugin {plugin_name} not found",
            "plugin": plugin_name
        }
    
    async def analyze_plugin_health(self) -> Dict[str, Any]:
        """Analyze the health of installed plugins.
        
        Returns:
            Dictionary containing plugin health analysis
        """
        plugins = await self.get_installed_plugins()
        
        analysis = {
            "total_plugins": 0,
            "active_plugins": 0,
            "inactive_plugins": 0,
            "failed_plugins": [],
            "outdated_plugins": [],
            "security_warnings": []
        }
        
        for plugin in plugins.get("plugins", []):
            analysis["total_plugins"] += 1
            
            if plugin.get("active", False):
                analysis["active_plugins"] += 1
            else:
                analysis["inactive_plugins"] += 1
                analysis["failed_plugins"].append({
                    "name": plugin["shortName"],
                    "error": plugin.get("failedError")
                })
            
            if plugin.get("hasUpdate", False):
                analysis["outdated_plugins"].append({
                    "name": plugin["shortName"],
                    "current_version": plugin.get("version"),
                    "latest_version": plugin.get("latestVersion")
                })
            
            if plugin.get("securityWarnings", []):
                analysis["security_warnings"].append({
                    "name": plugin["shortName"],
                    "warnings": plugin["securityWarnings"]
                })
        
        return analysis