"""Command-line interface for Jenkins Agent."""
import click
import asyncio
import json
import os
from typing import Optional, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
import httpx
from ..config.config import config

# Initialize rich console
console = Console()

# Configuration file
CONFIG_DIR = os.path.expanduser("~/.jenkins-cli")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
HISTORY_FILE = os.path.join(CONFIG_DIR, "history.json")

def load_config() -> Dict[str, Any]:
    """Load CLI configuration."""
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config_data: Dict[str, Any]) -> None:
    """Save CLI configuration."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f, indent=2)

def load_history() -> List[Dict[str, Any]]:
    """Load command history."""
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, 'r') as f:
        return json.load(f)

def save_history(command: str, result: Dict[str, Any]) -> None:
    """Save command to history."""
    history = load_history()
    history.append({
        "command": command,
        "result": result,
        "timestamp": datetime.now().isoformat()
    })
    # Keep last 100 commands
    history = history[-100:]
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

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
    # Create config directory if it doesn't exist
    os.makedirs(CONFIG_DIR, exist_ok=True)

@cli.group()
def config():
    """Manage CLI configuration."""
    pass

@config.command()
@click.option("--url", prompt=True, help="Jenkins API URL")
@click.option("--username", prompt=True, help="Jenkins username")
@click.option("--token", prompt=True, hide_input=True, help="Jenkins API token")
def setup(url: str, username: str, token: str):
    """Configure CLI settings."""
    config_data = {
        "url": url,
        "username": username,
        "token": token
    }
    save_config(config_data)
    console.print("[green]Configuration saved successfully![/green]")

@config.command()
def view():
    """View current configuration."""
    config_data = load_config()
    if not config_data:
        console.print("[yellow]No configuration found. Run 'config setup' first.[/yellow]")
        return
    
    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    for key, value in config_data.items():
        if key == "token":
            value = "********"
        table.add_row(key, value)
    
    console.print(table)

@cli.group()
def history():
    """Manage command history."""
    pass

@history.command(name="list")
@click.option("--limit", default=10, help="Number of entries to show")
def list_history(limit: int):
    """List command history."""
    history_data = load_history()
    if not history_data:
        console.print("[yellow]No history found.[/yellow]")
        return
    
    table = Table(title="Command History")
    table.add_column("Time", style="cyan")
    table.add_column("Command", style="green")
    table.add_column("Status", style="magenta")
    
    for entry in history_data[-limit:]:
        table.add_row(
            entry["timestamp"],
            entry["command"],
            entry["result"].get("status", "unknown")
        )
    
    console.print(table)

@history.command()
def clear():
    """Clear command history."""
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    console.print("[green]History cleared successfully![/green]")

@cli.group()
def monitor():
    """Monitor Jenkins status."""
    pass

@monitor.command()
@click.option("--refresh", default=5, help="Refresh interval in seconds")
def status(refresh: int):
    """Monitor Jenkins status in real-time."""
    def get_status_table() -> Table:
        table = Table(title="Jenkins Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="yellow")
        return table
    
    with Live(get_status_table(), refresh=True) as live:
        while True:
            table = get_status_table()
            try:
                # Get status from API
                client = JenkinsCLI()
                result = asyncio.run(client.execute_task("get system status"))
                if result and result.get("status") == "success":
                    status_data = result["result"]
                    table.add_row("System", "Online", "✓")
                    table.add_row(
                        "Active Tasks",
                        str(status_data.get("active_tasks", 0)),
                        ""
                    )
                    table.add_row(
                        "Agents",
                        str(status_data.get("active_agents", 0)),
                        ""
                    )
                else:
                    table.add_row("System", "Error", "Failed to get status")
            except Exception as e:
                table.add_row("System", "Error", str(e))
            
            live.update(table)
            time.sleep(refresh)

@cli.group()
def completion():
    """Shell completion commands."""
    pass

@completion.command()
@click.argument('shell', type=click.Choice(['bash', 'zsh', 'fish']))
def install(shell: str):
    """Install shell completion."""
    click.echo(f"Installing {shell} completion...")
    os.system(f"_{shell.upper()}_COMPLETE=source_{shell} jenkins-cli > ~/.{shell}_completion")
    click.echo(f"Add this to your ~/.{shell}rc:")
    click.echo(f"source ~/.{shell}_completion")

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