from typing import Dict, Any, Optional, List
import aiohttp
import logging
from langchain_jenkins.utils.config import config

logger = logging.getLogger(__name__)

class GitHubAPI:
    """GitHub API client."""
    
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.session = None
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {config.github.token}",
            "User-Agent": "LangChain-Jenkins-Agent"
        }
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)
    
    async def create_status(
        self,
        repo: str,
        sha: str,
        state: str,
        description: Optional[str] = None,
        context: Optional[str] = None,
        target_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a commit status."""
        await self._ensure_session()
        
        url = f"{self.base_url}/repos/{repo}/statuses/{sha}"
        data = {
            "state": state,
            "description": description or "",
            "context": context or "jenkins/langchain"
        }
        if target_url:
            data["target_url"] = target_url
            
        async with self.session.post(url, json=data) as response:
            if response.status != 201:
                text = await response.text()
                logger.error(f"Failed to create status: {text}")
                response.raise_for_status()
            return await response.json()
    
    async def create_comment(
        self,
        repo: str,
        issue_number: int,
        body: str
    ) -> Dict[str, Any]:
        """Create an issue or PR comment."""
        await self._ensure_session()
        
        url = f"{self.base_url}/repos/{repo}/issues/{issue_number}/comments"
        data = {"body": body}
        
        async with self.session.post(url, json=data) as response:
            if response.status != 201:
                text = await response.text()
                logger.error(f"Failed to create comment: {text}")
                response.raise_for_status()
            return await response.json()
    
    async def get_pull_request(
        self,
        repo: str,
        pr_number: int
    ) -> Dict[str, Any]:
        """Get pull request details."""
        await self._ensure_session()
        
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}"
        
        async with self.session.get(url) as response:
            if response.status != 200:
                text = await response.text()
                logger.error(f"Failed to get PR: {text}")
                response.raise_for_status()
            return await response.json()
    
    async def get_files(
        self,
        repo: str,
        sha: str
    ) -> List[Dict[str, Any]]:
        """Get files changed in a commit."""
        await self._ensure_session()
        
        url = f"{self.base_url}/repos/{repo}/commits/{sha}"
        
        async with self.session.get(url) as response:
            if response.status != 200:
                text = await response.text()
                logger.error(f"Failed to get files: {text}")
                response.raise_for_status()
            data = await response.json()
            return data.get('files', [])
    
    async def create_workflow_dispatch(
        self,
        repo: str,
        workflow_id: str,
        ref: str,
        inputs: Optional[Dict[str, Any]] = None
    ) -> None:
        """Trigger a GitHub Actions workflow."""
        await self._ensure_session()
        
        url = f"{self.base_url}/repos/{repo}/actions/workflows/{workflow_id}/dispatches"
        data = {
            "ref": ref,
            "inputs": inputs or {}
        }
        
        async with self.session.post(url, json=data) as response:
            if response.status != 204:
                text = await response.text()
                logger.error(f"Failed to trigger workflow: {text}")
                response.raise_for_status()
    
    async def get_workflow_runs(
        self,
        repo: str,
        workflow_id: str,
        branch: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get workflow runs."""
        await self._ensure_session()
        
        url = f"{self.base_url}/repos/{repo}/actions/workflows/{workflow_id}/runs"
        params = {}
        if branch:
            params['branch'] = branch
            
        async with self.session.get(url, params=params) as response:
            if response.status != 200:
                text = await response.text()
                logger.error(f"Failed to get workflow runs: {text}")
                response.raise_for_status()
            data = await response.json()
            return data.get('workflow_runs', [])