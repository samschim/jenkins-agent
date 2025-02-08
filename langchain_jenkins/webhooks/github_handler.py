from typing import Dict, Any
import hmac
import hashlib
import json
import logging
from fastapi import HTTPException, Request
from langchain_jenkins.agents.supervisor import SupervisorAgent
from langchain_jenkins.utils.config import config
from langchain_jenkins.utils.github import GitHubAPI

logger = logging.getLogger(__name__)

class GitHubWebhookHandler:
    """Handler for GitHub webhooks."""
    
    def __init__(self):
        self.supervisor = SupervisorAgent()
        self.github = GitHubAPI()
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify GitHub webhook signature."""
        if not signature:
            return False
            
        sha_name, signature = signature.split('=')
        if sha_name != 'sha256':
            return False
            
        mac = hmac.new(
            config.github.webhook_secret.encode(),
            msg=payload,
            digestmod=hashlib.sha256
        )
        return hmac.compare_digest(mac.hexdigest(), signature)
    
    async def handle_push(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle push event."""
        repo_name = data['repository']['full_name']
        branch = data['ref'].split('/')[-1]
        commit = data['head_commit']
        
        # Create task description for LangChain agent
        task = f"""
        Process GitHub push event:
        - Repository: {repo_name}
        - Branch: {branch}
        - Commit: {commit['message']}
        - Author: {commit['author']['name']}
        - Files changed: {', '.join([f['filename'] for f in commit['modified']])}
        
        Actions needed:
        1. Analyze changes and determine required pipeline steps
        2. Create or update Jenkins pipeline
        3. Trigger build if necessary
        4. Update GitHub status
        """
        
        result = await self.supervisor.handle_task(task)
        
        # Update GitHub status
        await self.github.create_status(
            repo=repo_name,
            sha=commit['id'],
            state='success' if result['status'] == 'success' else 'failure',
            description=result.get('message', 'Processed by LangChain agent'),
            context='jenkins/langchain'
        )
        
        return result
    
    async def handle_pull_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pull request event."""
        repo_name = data['repository']['full_name']
        pr = data['pull_request']
        action = data['action']
        
        task = f"""
        Process GitHub pull request event:
        - Repository: {repo_name}
        - PR: #{pr['number']} - {pr['title']}
        - Action: {action}
        - Author: {pr['user']['login']}
        - Base: {pr['base']['ref']}
        - Head: {pr['head']['ref']}
        
        Actions needed:
        1. Analyze PR changes and requirements
        2. Set up test environment if needed
        3. Configure and run tests
        4. Update PR status and comments
        """
        
        result = await self.supervisor.handle_task(task)
        
        # Add PR comment with results
        if result['status'] == 'success':
            comment = f"""
            ✅ LangChain agent processed this PR:
            
            {result.get('message', '')}
            
            <details>
            <summary>Details</summary>
            
            ```json
            {json.dumps(result, indent=2)}
            ```
            </details>
            """
        else:
            comment = f"""
            ❌ LangChain agent encountered an issue:
            
            {result.get('error', 'Unknown error')}
            
            Please check the logs for more details.
            """
        
        await self.github.create_comment(
            repo=repo_name,
            pr_number=pr['number'],
            body=comment
        )
        
        return result
    
    async def handle_issue(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle issue event."""
        repo_name = data['repository']['full_name']
        issue = data['issue']
        action = data['action']
        
        task = f"""
        Process GitHub issue event:
        - Repository: {repo_name}
        - Issue: #{issue['number']} - {issue['title']}
        - Action: {action}
        - Author: {issue['user']['login']}
        - Labels: {', '.join(label['name'] for label in issue['labels'])}
        
        Actions needed:
        1. Analyze issue content and labels
        2. Determine required actions
        3. Update Jenkins configuration if needed
        4. Respond to issue
        """
        
        result = await self.supervisor.handle_task(task)
        
        # Add issue comment with results
        comment = f"""
        🤖 LangChain agent response:
        
        {result.get('message', result.get('error', 'No message'))}
        
        <details>
        <summary>Technical Details</summary>
        
        ```json
        {json.dumps(result, indent=2)}
        ```
        </details>
        """
        
        await self.github.create_comment(
            repo=repo_name,
            issue_number=issue['number'],
            body=comment
        )
        
        return result
    
    async def handle_webhook(self, request: Request) -> Dict[str, Any]:
        """Handle GitHub webhook."""
        payload = await request.body()
        signature = request.headers.get('X-Hub-Signature-256')
        
        if not self.verify_signature(payload, signature):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        event_type = request.headers.get('X-GitHub-Event')
        data = json.loads(payload)
        
        handlers = {
            'push': self.handle_push,
            'pull_request': self.handle_pull_request,
            'issues': self.handle_issue
        }
        
        handler = handlers.get(event_type)
        if not handler:
            logger.warning(f"Unhandled event type: {event_type}")
            return {"status": "ignored", "event": event_type}
        
        try:
            result = await handler(data)
            logger.info(f"Processed {event_type} event: {result}")
            return result
        except Exception as e:
            logger.error(f"Error processing {event_type} event: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))