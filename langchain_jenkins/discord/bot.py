"""Discord bot for Jenkins Agent."""
import os
import asyncio
import discord
from discord import app_commands
from typing import Optional
import httpx
from ..config.config import config

class JenkinsBot(discord.Client):
    """Discord bot for Jenkins Agent."""
    
    def __init__(self):
        """Initialize Discord bot."""
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        
        # API client
        self.base_url = "http://localhost:8000"  # FastAPI server
        self.token = None
        
        # Command tree
        self.tree = app_commands.CommandTree(self)
    
    async def setup_hook(self):
        """Set up bot hooks."""
        # Login to Jenkins Agent
        await self.login_to_jenkins()
        
        # Sync commands
        await self.tree.sync()
    
    async def login_to_jenkins(self):
        """Login to Jenkins Agent API."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/token",
                    data={
                        "username": config.jenkins.user,
                        "password": config.jenkins.api_token
                    }
                )
                if response.status_code == 200:
                    self.token = response.json()["access_token"]
                    print("Successfully logged in to Jenkins Agent API")
                else:
                    print("Failed to login to Jenkins Agent API")
            except Exception as e:
                print(f"Error logging in to Jenkins Agent API: {e}")
    
    async def execute_task(
        self,
        task: str,
        agent_type: Optional[str] = None
    ) -> dict:
        """Execute a task using the API.
        
        Args:
            task: Task description
            agent_type: Optional agent type
            
        Returns:
            Task result
        """
        if not self.token:
            await self.login_to_jenkins()
            if not self.token:
                return {
                    "status": "error",
                    "message": "Not logged in to Jenkins Agent API"
                }
        
        headers = {"Authorization": f"Bearer {self.token}"}
        data = {"task": task}
        if agent_type:
            data["agent_type"] = agent_type
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/task",
                    headers=headers,
                    json=data
                )
                return response.json()
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Task execution failed: {e}"
                }
    
    async def list_agents(self) -> dict:
        """List available agents."""
        if not self.token:
            await self.login_to_jenkins()
            if not self.token:
                return {
                    "status": "error",
                    "message": "Not logged in to Jenkins Agent API"
                }
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/agents",
                    headers=headers
                )
                return response.json()
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Failed to list agents: {e}"
                }

# Create bot instance
bot = JenkinsBot()

@bot.tree.command(name="task", description="Execute a Jenkins task")
async def task_command(
    interaction: discord.Interaction,
    task: str,
    agent: Optional[str] = None
):
    """Execute a Jenkins task.
    
    Args:
        interaction: Discord interaction
        task: Task description
        agent: Optional agent type
    """
    await interaction.response.defer()
    
    result = await bot.execute_task(task, agent)
    
    if result["status"] == "success":
        # Create embed for success
        embed = discord.Embed(
            title="Task Completed",
            description=task,
            color=discord.Color.green()
        )
        embed.add_field(
            name="Result",
            value=f"```json\n{str(result['result'])[:1000]}```"
        )
        if agent:
            embed.add_field(name="Agent", value=agent)
    else:
        # Create embed for error
        embed = discord.Embed(
            title="Task Failed",
            description=task,
            color=discord.Color.red()
        )
        embed.add_field(
            name="Error",
            value=result.get("message", "Unknown error")
        )
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="agents", description="List available Jenkins agents")
async def agents_command(interaction: discord.Interaction):
    """List available Jenkins agents.
    
    Args:
        interaction: Discord interaction
    """
    await interaction.response.defer()
    
    result = await bot.list_agents()
    
    if "agents" in result:
        # Create embed for agent list
        embed = discord.Embed(
            title="Available Agents",
            color=discord.Color.blue()
        )
        for agent in result["agents"]:
            embed.add_field(
                name=agent["type"],
                value=agent["description"],
                inline=False
            )
    else:
        # Create embed for error
        embed = discord.Embed(
            title="Error",
            description="Failed to list agents",
            color=discord.Color.red()
        )
        embed.add_field(
            name="Error",
            value=result.get("message", "Unknown error")
        )
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="help", description="Show Jenkins bot help")
async def help_command(interaction: discord.Interaction):
    """Show help information.
    
    Args:
        interaction: Discord interaction
    """
    embed = discord.Embed(
        title="Jenkins Bot Help",
        description="Available commands:",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="/task <description> [agent]",
        value="Execute a Jenkins task",
        inline=False
    )
    embed.add_field(
        name="/agents",
        value="List available agents",
        inline=False
    )
    embed.add_field(
        name="/help",
        value="Show this help message",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed)

def run_bot():
    """Run the Discord bot."""
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("Error: DISCORD_TOKEN environment variable not set")
        return
    
    bot.run(token)