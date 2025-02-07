"""User management tools for Jenkins."""
from typing import Dict, Any, List, Optional
from .jenkins_api import JenkinsAPI

class UserTools:
    """Tools for managing Jenkins users and permissions."""
    
    def __init__(self):
        """Initialize user tools with Jenkins API client."""
        self.jenkins = JenkinsAPI()
    
    async def get_users(self) -> Dict[str, Any]:
        """Get information about Jenkins users.
        
        Returns:
            Dictionary containing user information
        """
        return await self.jenkins._request(
            "GET",
            "/asynchPeople/api/json?depth=2"
        )
    
    async def create_user(
        self,
        username: str,
        password: str,
        fullname: str,
        email: str
    ) -> Dict[str, Any]:
        """Create a new Jenkins user.
        
        Args:
            username: Username for the new user
            password: Password for the new user
            fullname: Full name of the user
            email: Email address of the user
            
        Returns:
            User creation status
        """
        data = {
            "username": username,
            "password1": password,
            "password2": password,
            "fullname": fullname,
            "email": email
        }
        
        response = await self.jenkins._request(
            "POST",
            "/securityRealm/createAccount",
            data=data
        )
        
        return {
            "status": "success",
            "message": f"User {username} created successfully",
            "username": username
        }
    
    async def delete_user(self, username: str) -> Dict[str, Any]:
        """Delete a Jenkins user.
        
        Args:
            username: Username to delete
            
        Returns:
            User deletion status
        """
        response = await self.jenkins._request(
            "POST",
            f"/user/{username}/doDelete"
        )
        
        return {
            "status": "success",
            "message": f"User {username} deleted successfully",
            "username": username
        }
    
    async def get_user_permissions(
        self,
        username: str
    ) -> Dict[str, Any]:
        """Get permissions for a user.
        
        Args:
            username: Username to check permissions for
            
        Returns:
            Dictionary containing user permissions
        """
        response = await self.jenkins._request(
            "GET",
            f"/user/{username}/api/json?depth=2"
        )
        
        return {
            "username": username,
            "permissions": response.get("permissions", []),
            "roles": response.get("roles", [])
        }
    
    async def grant_permission(
        self,
        username: str,
        permission: str
    ) -> Dict[str, Any]:
        """Grant a permission to a user.
        
        Args:
            username: Username to grant permission to
            permission: Permission to grant
            
        Returns:
            Permission grant status
        """
        data = {
            "username": username,
            "permission": permission
        }
        
        response = await self.jenkins._request(
            "POST",
            "/role-strategy/strategy/assignRole",
            data=data
        )
        
        return {
            "status": "success",
            "message": f"Permission {permission} granted to {username}",
            "username": username,
            "permission": permission
        }
    
    async def revoke_permission(
        self,
        username: str,
        permission: str
    ) -> Dict[str, Any]:
        """Revoke a permission from a user.
        
        Args:
            username: Username to revoke permission from
            permission: Permission to revoke
            
        Returns:
            Permission revocation status
        """
        data = {
            "username": username,
            "permission": permission
        }
        
        response = await self.jenkins._request(
            "POST",
            "/role-strategy/strategy/unassignRole",
            data=data
        )
        
        return {
            "status": "success",
            "message": f"Permission {permission} revoked from {username}",
            "username": username,
            "permission": permission
        }
    
    async def get_api_token(self, username: str) -> Dict[str, Any]:
        """Get or generate API token for a user.
        
        Args:
            username: Username to get token for
            
        Returns:
            API token information
        """
        response = await self.jenkins._request(
            "POST",
            f"/user/{username}/descriptorByName/jenkins.security.ApiTokenProperty/generateNewToken",
            data={"newTokenName": "auto-generated"}
        )
        
        return {
            "status": "success",
            "username": username,
            "token": response.get("data", {}).get("tokenValue"),
            "token_name": "auto-generated"
        }
    
    async def analyze_user_activity(
        self,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze user activity.
        
        Args:
            username: Optional username to analyze specific user
            
        Returns:
            User activity analysis
        """
        if username:
            response = await self.jenkins._request(
                "GET",
                f"/user/{username}/api/json?depth=2"
            )
            
            return {
                "username": username,
                "last_login": response.get("lastLogin"),
                "project_permissions": response.get("projectPermissions", []),
                "build_history": response.get("builds", [])
            }
        else:
            users = await self.get_users()
            analysis = {
                "total_users": len(users.get("users", [])),
                "active_users": 0,
                "inactive_users": 0,
                "user_activity": []
            }
            
            for user in users.get("users", []):
                user_data = await self.analyze_user_activity(user["user"]["fullName"])
                if user_data.get("last_login"):
                    analysis["active_users"] += 1
                else:
                    analysis["inactive_users"] += 1
                analysis["user_activity"].append(user_data)
            
            return analysis
    
    async def audit_permissions(self) -> Dict[str, Any]:
        """Audit all user permissions.
        
        Returns:
            Permission audit results
        """
        users = await self.get_users()
        audit = {
            "users": [],
            "permission_summary": {},
            "potential_issues": []
        }
        
        for user in users.get("users", []):
            username = user["user"]["fullName"]
            permissions = await self.get_user_permissions(username)
            
            # Add to user list
            audit["users"].append({
                "username": username,
                "permissions": permissions["permissions"]
            })
            
            # Update permission summary
            for perm in permissions["permissions"]:
                if perm not in audit["permission_summary"]:
                    audit["permission_summary"][perm] = 0
                audit["permission_summary"][perm] += 1
            
            # Check for potential issues
            if "Overall/Administer" in permissions["permissions"]:
                audit["potential_issues"].append({
                    "username": username,
                    "issue": "Has administrator privileges"
                })
        
        return audit