"""Interactive chat mode for Jenkins agent."""
import sys
import asyncio
import aioconsole
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax
from ..agents.supervisor import SupervisorAgent

console = Console()

class InteractiveChat:
    """Interactive chat interface for Jenkins agent."""
    
    def __init__(self):
        """Initialize chat interface."""
        self.supervisor = SupervisorAgent()
        self.history = []
    
    def _format_code(self, text: str) -> str:
        """Format code blocks in text."""
        if "```" in text:
            parts = text.split("```")
            formatted = []
            for i, part in enumerate(parts):
                if i % 2 == 0:  # Not code block
                    formatted.append(part)
                else:  # Code block
                    lang = part.split("\n")[0]
                    code = "\n".join(part.split("\n")[1:])
                    syntax = Syntax(code, lang or "python", theme="monokai")
                    formatted.append(str(syntax))
            return "\n".join(formatted)
        return text
    
    def _display_response(self, response: dict):
        """Display agent response."""
        if response["status"] == "success":
            if "pipeline" in response:
                console.print(Panel(
                    Syntax(response["pipeline"], "groovy", theme="monokai"),
                    title="Generated Pipeline",
                    border_style="green"
                ))
            elif "analysis" in response:
                console.print(Panel(
                    Markdown(response["analysis"]),
                    title="Analysis Results",
                    border_style="blue"
                ))
            elif "metrics" in response:
                console.print(Panel(
                    Markdown(str(response["metrics"])),
                    title="System Metrics",
                    border_style="cyan"
                ))
            
            if "recommendations" in response:
                console.print(Panel(
                    Markdown("\n".join(f"- {r}" for r in response["recommendations"])),
                    title="Recommendations",
                    border_style="yellow"
                ))
            
            if "message" in response:
                console.print(f"[green]{response['message']}[/green]")
        else:
            console.print(f"[red]Error: {response.get('error', 'Unknown error')}[/red]")
    
    def _display_help(self):
        """Display help information."""
        help_text = """
# Available Commands

## General
- `help`: Show this help message
- `exit`: Exit the chat
- `history`: Show command history
- `clear`: Clear the screen

## Jenkins Management
- Create/manage jobs: "Create a new build job for Python project"
- Manage pipelines: "Create a pipeline with testing and deployment"
- Analyze logs: "Analyze build logs for my-project"
- Check status: "Get status of my-project"
- Install plugins: "Install git plugin"

## Advanced Features
- Get insights: "Show system metrics and insights"
- Optimize: "Optimize my-pipeline for better performance"
- Security: "Scan my-pipeline for security issues"
- Complex tasks: "Create pipeline and analyze its first build"

## Tips
- Use natural language to describe what you want to do
- For complex tasks, be specific about requirements
- Check recommendations for improvements
"""
        console.print(Markdown(help_text))
    
    async def start(self):
        """Start interactive chat session."""
        console.print(Panel(
            "[bold blue]Jenkins Agent Interactive Chat[/bold blue]\n"
            "Type 'help' for available commands or 'exit' to quit",
            border_style="blue"
        ))
        
        while True:
            try:
                # Get user input
                command = await aioconsole.ainput("[bold green]> [/bold green]")
                
                # Handle special commands
                if not command:
                    continue
                elif command.lower() == "exit":
                    break
                elif command.lower() == "help":
                    self._display_help()
                    continue
                elif command.lower() == "history":
                    for i, cmd in enumerate(self.history, 1):
                        console.print(f"{i}. {cmd}")
                    continue
                elif command.lower() == "clear":
                    console.clear()
                    continue
                
                # Add to history
                self.history.append(command)
                
                # Process command
                with console.status("[bold blue]Processing...[/bold blue]"):
                    if "and" in command.lower():
                        response = await self.supervisor.handle_complex_task(command)
                    else:
                        response = await self.supervisor.handle_task(command)
                
                # Display response
                self._display_response(response)
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'exit' to quit[/yellow]")
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
    
    @classmethod
    async def run(cls):
        """Run the interactive chat."""
        chat = cls()
        await chat.start()

def main():
    """Main entry point for interactive chat."""
    try:
        asyncio.run(InteractiveChat.run())
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()