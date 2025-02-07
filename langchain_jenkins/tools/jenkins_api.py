"""Jenkins API tools for LangChain agents."""
import httpx
from typing import Dict, Any, Optional
from ..config.config import config

class JenkinsAPI:
    """Jenkins API client for interacting with Jenkins server."""
    
    def __init__(self):
        """Initialize Jenkins API client."""
        self.base_url = config.jenkins.url
        self.auth = (config.jenkins.user, config.jenkins.api_token)
        self.verify_ssl = config.jenkins.verify_ssl
        
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to Jenkins API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request data for POST/PUT requests
            params: Query parameters
            
        Returns:
            API response as dictionary
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        async with httpx.AsyncClient(verify=self.verify_ssl) as client:
            response = await client.request(
                method=method,
                url=url,
                auth=self.auth,
                json=data,
                params=params
            )
            response.raise_for_status()
            return response.json() if response.content else {}

    async def get_job_info(self, job_name: str) -> Dict[str, Any]:
        """Get information about a Jenkins job.
        
        Args:
            job_name: Name of the Jenkins job
            
        Returns:
            Job information
        """
        return await self._request("GET", f"/job/{job_name}/api/json")

    async def build_job(
        self,
        job_name: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Trigger a build for a Jenkins job.
        
        Args:
            job_name: Name of the Jenkins job
            parameters: Build parameters
            
        Returns:
            Build information
        """
        endpoint = f"/job/{job_name}/build"
        if parameters:
            endpoint = f"/job/{job_name}/buildWithParameters"
        return await self._request("POST", endpoint, data=parameters)

    async def get_build_log(self, job_name: str, build_number: str = "lastBuild") -> str:
        """Get the console log for a build.
        
        Args:
            job_name: Name of the Jenkins job
            build_number: Build number or "lastBuild"
            
        Returns:
            Build console log
        """
        endpoint = f"/job/{job_name}/{build_number}/consoleText"
        async with httpx.AsyncClient(verify=self.verify_ssl) as client:
            response = await client.get(
                f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}",
                auth=self.auth
            )
            response.raise_for_status()
            return response.text

    async def get_plugins(self) -> Dict[str, Any]:
        """Get information about installed plugins.
        
        Returns:
            Plugin information
        """
        return await self._request("GET", "/pluginManager/api/json?depth=1")

    async def get_system_info(self) -> Dict[str, Any]:
        """Get Jenkins system information.
        
        Returns:
            System information
        """
        return await self._request("GET", "/api/json?tree=numExecutors,description,jobs[name,color]")