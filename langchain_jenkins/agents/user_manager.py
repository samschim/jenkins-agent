"""User manager agent for handling Jenkins users."""
from typing import Dict, Any, List
from langchain.tools import Tool
from .base_agent import BaseAgent
from ..tools.user_tools import UserTools

class UserManagerAgent(BaseAgent):
    """Agent for managing Jenkins users."""
    
    def __init__(self):
        """Initialize user manager agent with required tools."""
        self.user_tools = UserTools()
        
        tools = [
            Tool(
                name="GetUsers",
                func=self.user_tools.get_users,
                description="Get information about Jenkins users"
            ),
            Tool(
                name="CreateUser",
                func=self.user_tools.create_user,
                description="Create a new Jenkins user"
            ),
            Tool(
                name="DeleteUser",
                func=self.user_tools.delete_user,
                description="Delete a Jenkins user"
            ),
            Tool(
                name="GetUserPermissions",
                func=self.user_tools.get_user_permissions,
                description="Get permissions for a user"
            ),
            Tool(
                name="GrantPermission",
                func=self.user_tools.grant_permission,
                description="Grant a permission to a user"
            ),
            Tool(
                name="RevokePermission",
                func=self.user_tools.revoke_permission,
                description="Revoke a permission from a user"
            ),
            Tool(
                name="GetApiToken",
                func=self.user_tools.get_api_token,
                description="Get or generate API token for a user"
            ),
            Tool(
                name="AnalyzeUserActivity",
                func=self.user_tools.analyze_user_activity,
                description="Analyze user activity"
            ),
            Tool(
                name="AuditPermissions",
                func=self.user_tools.audit_permissions,
                description="Audit all user permissions"
            )
        ]
        
        super().__init__(tools)
    
    async def handle_task(self, task: str) -> Dict[str, Any]:
        """Handle user-related tasks.
        
        Args:
            task: Description of the user task to perform
            
        Returns:
            Result of the task execution
        """
        task_lower = task.lower()
        
        if "create" in task_lower:
            return await self._handle_user_creation(task)
        elif "delete" in task_lower or "remove" in task_lower:
            return await self._handle_user_deletion(task)
        elif "permission" in task_lower:
            if "grant" in task_lower or "add" in task_lower:
                return await self._handle_permission_grant(task)
            elif "revoke" in task_lower or "remove" in task_lower:
                return await self._handle_permission_revoke(task)
            else:
                return await self._handle_permission_check(task)
        elif "token" in task_lower:
            return await self._handle_api_token(task)
        elif "activity" in task_lower or "analyze" in task_lower:
            return await self._handle_user_activity(task)
        elif "audit" in task_lower:
            return await self._handle_permission_audit(task)
        elif "list" in task_lower or "show" in task_lower:
            return await self._handle_user_list(task)
        else:
            return {
                "status": "error",
                "error": "Unsupported user task",
                "task": task
            }
    
    async def _handle_user_creation(self, task: str) -> Dict[str, Any]:
        """Handle user creation tasks.
        
        Args:
            task: User creation task description
            
        Returns:
            User creation results
        """
        # This is a simplified implementation
        # In a real system, you'd want more sophisticated parsing
        words = task.split()
        username = next(
            (word for word in words if "user" not in word.lower()),
            None
        )
        
        if not username:
            return {
                "status": "error",
                "error": "No username specified",
                "task": task
            }
        
        try:
            # For demo purposes, using default values
            result = await self.user_tools.create_user(
                username=username,
                password="defaultPassword123",  # In practice, this should be generated
                fullname=username.title(),
                email=f"{username}@example.com"
            )
            
            return {
                "status": "success",
                "user_creation": result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "username": username
            }
    
    async def _handle_user_deletion(self, task: str) -> Dict[str, Any]:
        """Handle user deletion tasks.
        
        Args:
            task: User deletion task description
            
        Returns:
            User deletion results
        """
        words = task.split()
        username = next(
            (word for word in words if "user" not in word.lower()),
            None
        )
        
        if not username:
            return {
                "status": "error",
                "error": "No username specified",
                "task": task
            }
        
        try:
            result = await self.user_tools.delete_user(username)
            return {
                "status": "success",
                "user_deletion": result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "username": username
            }
    
    async def _handle_permission_grant(self, task: str) -> Dict[str, Any]:
        """Handle permission grant tasks.
        
        Args:
            task: Permission grant task description
            
        Returns:
            Permission grant results
        """
        # Extract username and permission from task
        words = task.split()
        username = next(
            (word for word in words if "user" not in word.lower()),
            None
        )
        permission = next(
            (word for word in words if "permission" not in word.lower()),
            None
        )
        
        if not username or not permission:
            return {
                "status": "error",
                "error": "Missing username or permission",
                "task": task
            }
        
        try:
            result = await self.user_tools.grant_permission(
                username,
                permission
            )
            return {
                "status": "success",
                "permission_grant": result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "username": username,
                "permission": permission
            }
    
    async def _handle_permission_revoke(self, task: str) -> Dict[str, Any]:
        """Handle permission revocation tasks.
        
        Args:
            task: Permission revocation task description
            
        Returns:
            Permission revocation results
        """
        # Extract username and permission from task
        words = task.split()
        username = next(
            (word for word in words if "user" not in word.lower()),
            None
        )
        permission = next(
            (word for word in words if "permission" not in word.lower()),
            None
        )
        
        if not username or not permission:
            return {
                "status": "error",
                "error": "Missing username or permission",
                "task": task
            }
        
        try:
            result = await self.user_tools.revoke_permission(
                username,
                permission
            )
            return {
                "status": "success",
                "permission_revocation": result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "username": username,
                "permission": permission
            }
    
    async def _handle_permission_check(self, task: str) -> Dict[str, Any]:
        """Handle permission check tasks.
        
        Args:
            task: Permission check task description
            
        Returns:
            Permission check results
        """
        words = task.split()
        username = next(
            (word for word in words if "user" not in word.lower()),
            None
        )
        
        if not username:
            return {
                "status": "error",
                "error": "No username specified",
                "task": task
            }
        
        try:
            permissions = await self.user_tools.get_user_permissions(username)
            return {
                "status": "success",
                "username": username,
                "permissions": permissions
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "username": username
            }
    
    async def _handle_api_token(self, task: str) -> Dict[str, Any]:
        """Handle API token tasks.
        
        Args:
            task: API token task description
            
        Returns:
            API token results
        """
        words = task.split()
        username = next(
            (word for word in words if "user" not in word.lower()),
            None
        )
        
        if not username:
            return {
                "status": "error",
                "error": "No username specified",
                "task": task
            }
        
        try:
            token = await self.user_tools.get_api_token(username)
            return {
                "status": "success",
                "api_token": token
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "username": username
            }
    
    async def _handle_user_activity(self, task: str) -> Dict[str, Any]:
        """Handle user activity analysis tasks.
        
        Args:
            task: User activity task description
            
        Returns:
            Activity analysis results
        """
        words = task.split()
        username = next(
            (word for word in words if "user" not in word.lower()),
            None
        )
        
        try:
            if username:
                activity = await self.user_tools.analyze_user_activity(username)
            else:
                activity = await self.user_tools.analyze_user_activity()
            
            return {
                "status": "success",
                "activity_analysis": activity
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "username": username if username else "all"
            }
    
    async def _handle_permission_audit(self, task: str) -> Dict[str, Any]:
        """Handle permission audit tasks.
        
        Args:
            task: Permission audit task description
            
        Returns:
            Audit results
        """
        try:
            audit = await self.user_tools.audit_permissions()
            return {
                "status": "success",
                "permission_audit": audit
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _handle_user_list(self, task: str) -> Dict[str, Any]:
        """Handle user listing tasks.
        
        Args:
            task: User list task description
            
        Returns:
            User list results
        """
        try:
            users = await self.user_tools.get_users()
            return {
                "status": "success",
                "users": users
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }