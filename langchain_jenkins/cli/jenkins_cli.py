"""Command-line interface for Jenkins Agent."""
import click
import asyncio
import json
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from rich.syntax import Syntax
from rich.panel import Panel
import httpx
from ..config.config import config

# Initialize rich console
console = Console()

class JenkinsCLI:
    """CLI client for Jenkins Agent."""
    
    def __init__(self):
        """Initialize CLI client."""
        self.base_url = "http://localhost:8000"  # FastAPI server
        self.token = None
    
    async def login(self, username: str, password: str) -> bool:
        """Login to get access token.
        
        Args:
            username: Jenkins username
            password: Jenkins password
            
        Returns:
            True if login successful
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/token",
                    data={
                        "username": username,
                        "password": password
                    }
                )
                if response.status_code == 200:
                    self.token = response.json()["access_token"]
                    return True
                return False
            except Exception as e:
                console.print(f"[red]Login failed: {e}[/red]")
                return False
    
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
            console.print("[red]Not logged in. Use 'login' command first.[/red]")
            return None
        
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
                console.print(f"[red]Task execution failed: {e}[/red]")
                return None
    
    async def list_agents(self) -> dict:
        """List available agents."""
        if not self.token:
            console.print("[red]Not logged in. Use 'login' command first.[/red]")
            return None
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/agents",
                    headers=headers
                )
                return response.json()
            except Exception as e:
                console.print(f"[red]Failed to list agents: {e}[/red]")
                return None

# CLI commands
@click.group()
def cli():
    """Jenkins Agent CLI - Interact with Jenkins through natural language."""
    pass

@cli.command()
@click.option("--username", prompt=True)
@click.option("--password", prompt=True, hide_input=True)
def login(username: str, password: str):
    """Login to Jenkins Agent."""
    client = JenkinsCLI()
    if asyncio.run(client.login(username, password)):
        console.print("[green]Login successful![/green]")
    else:
        console.print("[red]Login failed.[/red]")

@cli.command()
@click.argument("task")
@click.option("--agent", help="Specific agent type to use")
def task(task: str, agent: Optional[str] = None):
    """Execute a task."""
    client = JenkinsCLI()
    with Progress() as progress:
        task_id = progress.add_task("[cyan]Executing task...", total=None)
        result = asyncio.run(client.execute_task(task, agent))
        progress.remove_task(task_id)
    
    if result:
        if result["status"] == "success":
            console.print(Panel.fit(
                Syntax(
                    json.dumps(result["result"], indent=2),
                    "json",
                    theme="monokai"
                ),
                title="Task Result",
                border_style="green"
            ))
        else:
            console.print(Panel.fit(
                str(result),
                title="Task Failed",
                border_style="red"
            ))

@cli.command()
def agents():
    """List available agents."""
    client = JenkinsCLI()
    result = asyncio.run(client.list_agents())
    
    if result:
        table = Table(title="Available Agents")
        table.add_column("Type", style="cyan")
        table.add_column("Description", style="green")
        
        for agent in result["agents"]:
            table.add_row(agent["type"], agent["description"])
        
        console.print(table)

@cli.command()
def interactive():
    """Start interactive mode."""
    client = JenkinsCLI()
    console.print("[cyan]Welcome to Jenkins Agent Interactive Mode![/cyan]")
    console.print("Type 'exit' to quit, 'help' for commands.")
    
    while True:
        command = console.input("[green]jenkins> [/green]")
        if command.lower() == "exit":
            break
        elif command.lower() == "help":
            console.print(Panel.fit(
                "\n".join([
                    "Available commands:",
                    "  task <description> - Execute a task",
                    "  agents - List available agents",
                    "  help - Show this help",
                    "  exit - Exit interactive mode"
                ]),
                title="Help",
                border_style="blue"
            ))
        elif command.lower().startswith("task "):
            task_desc = command[5:].strip()
            result = asyncio.run(client.execute_task(task_desc))
            if result:
                console.print(Panel.fit(
                    Syntax(
                        json.dumps(result["result"], indent=2),
                        "json",
                        theme="monokai"
                    ),
                    title="Task Result",
                    border_style="green"
                ))
        elif command.lower() == "agents":
            result = asyncio.run(client.list_agents())
            if result:
                table = Table(title="Available Agents")
                table.add_column("Type", style="cyan")
                table.add_column("Description", style="green")
                
                for agent in result["agents"]:
                    table.add_row(agent["type"], agent["description"])
                
                console.print(table)
        else:
            console.print("[red]Unknown command. Type 'help' for available commands.[/red]")

if __name__ == "__main__":
    cli()