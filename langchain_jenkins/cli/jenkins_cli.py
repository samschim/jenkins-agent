"""Command line interface for Jenkins agent."""
import os
import sys
import click
import asyncio
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.panel import Panel
from ..agents.supervisor import SupervisorAgent

console = Console()

def run_async(func):
    """Decorator to run async functions."""
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))
    return wrapper

@click.group()
def cli():
    """Jenkins Agent CLI - Manage Jenkins with natural language."""
    pass

@cli.command()
def chat():
    """Start interactive chat mode."""
    from .interactive import main
    main()

@cli.command()
@click.argument('job_name')
@click.option('--type', '-t', default='java', help='Project type (java/python/node/docker)')
@click.option('--with-tests/--no-tests', default=True, help='Include test stage')
@click.option('--with-deploy/--no-deploy', default=False, help='Include deployment stage')
@run_async
async def create_job(job_name, type, with_tests, with_deploy):
    """Create a new Jenkins job."""
    supervisor = SupervisorAgent()
    
    requirements = []
    if with_tests:
        requirements.append("Include testing stage")
    if with_deploy:
        requirements.append("Include deployment stage")
    
    task = f"Create a new {type} job named {job_name}"
    if requirements:
        task += f" with {', '.join(requirements)}"
    
    with console.status("[bold blue]Creating job...[/bold blue]"):
        result = await supervisor.handle_task(task)
    
    if result["status"] == "success":
        console.print(f"[green]Created job {job_name}[/green]")
        if "pipeline" in result:
            console.print(Panel(
                Syntax(result["pipeline"], "groovy", theme="monokai"),
                title="Generated Pipeline",
                border_style="green"
            ))
    else:
        console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")

@cli.command()
@click.argument('job_name')
@click.option('--parameters', '-p', multiple=True, help='Build parameters (key=value)')
@run_async
async def build(job_name, parameters):
    """Trigger a build for a job."""
    supervisor = SupervisorAgent()
    
    params = {}
    for param in parameters:
        key, value = param.split('=', 1)
        params[key] = value
    
    task = f"Start build for {job_name}"
    if params:
        task += f" with parameters {params}"
    
    with console.status("[bold blue]Triggering build...[/bold blue]"):
        result = await supervisor.handle_task(task)
    
    if result["status"] == "success":
        console.print(f"[green]Build triggered for {job_name}[/green]")
        if "build_number" in result:
            console.print(f"Build number: {result['build_number']}")
    else:
        console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")

@cli.command()
@click.argument('job_name')
@run_async
async def analyze(job_name):
    """Analyze build logs for a job."""
    supervisor = SupervisorAgent()
    
    with console.status("[bold blue]Analyzing logs...[/bold blue]"):
        result = await supervisor.handle_task(f"Analyze logs for {job_name}")
    
    if result["status"] == "success":
        if "analysis" in result:
            console.print(Panel(
                Markdown(result["analysis"]),
                title=f"Log Analysis for {job_name}",
                border_style="blue"
            ))
        if "recommendations" in result:
            console.print(Panel(
                Markdown("\n".join(f"- {r}" for r in result["recommendations"])),
                title="Recommendations",
                border_style="yellow"
            ))
    else:
        console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")

@cli.command()
@click.argument('pipeline_name')
@run_async
async def optimize(pipeline_name):
    """Optimize a pipeline."""
    supervisor = SupervisorAgent()
    
    with console.status("[bold blue]Optimizing pipeline...[/bold blue]"):
        result = await supervisor.handle_task(f"Optimize {pipeline_name} for better performance")
    
    if result["status"] == "success":
        console.print(Panel(
            Syntax(result["optimized_pipeline"], "groovy", theme="monokai"),
            title="Optimized Pipeline",
            border_style="green"
        ))
        if "improvements" in result:
            console.print(Panel(
                Markdown("\n".join(f"- {i}" for i in result["improvements"])),
                title="Improvements Made",
                border_style="blue"
            ))
    else:
        console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")

@cli.command()
@click.argument('pipeline_name')
@run_async
async def scan(pipeline_name):
    """Scan a pipeline for security issues."""
    supervisor = SupervisorAgent()
    
    with console.status("[bold blue]Scanning pipeline...[/bold blue]"):
        result = await supervisor.handle_task(f"Scan {pipeline_name} for security issues")
    
    if result["status"] == "success":
        if "findings" in result:
            table = Table(title="Security Findings")
            table.add_column("Severity", style="bold")
            table.add_column("Issue")
            table.add_column("Location")
            
            for finding in result["findings"]:
                table.add_row(
                    finding["severity"],
                    finding["description"],
                    f"Line {finding['line']}"
                )
            
            console.print(table)
        
        if "recommendations" in result:
            console.print(Panel(
                Markdown("\n".join(f"- {r}" for r in result["recommendations"])),
                title="Security Recommendations",
                border_style="red"
            ))
    else:
        console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")

@cli.command()
@run_async
async def metrics():
    """Show system metrics and insights."""
    supervisor = SupervisorAgent()
    
    with console.status("[bold blue]Collecting metrics...[/bold blue]"):
        result = await supervisor.collect_metrics_and_insights()
    
    if result["status"] == "success":
        # Build metrics
        build_table = Table(title="Build Metrics")
        build_table.add_column("Metric", style="bold")
        build_table.add_column("Value")
        
        builds = result["metrics"]["builds"]
        build_table.add_row("Total Builds", str(builds.get("total_builds", 0)))
        build_table.add_row(
            "Success Rate",
            f"{builds.get('successful_builds', 0) / max(builds.get('total_builds', 1), 1) * 100:.1f}%"
        )
        build_table.add_row(
            "Average Duration",
            f"{builds.get('average_duration', 0) / 60:.1f} minutes"
        )
        
        console.print(build_table)
        
        # Pipeline metrics
        pipeline_table = Table(title="Pipeline Metrics")
        pipeline_table.add_column("Metric", style="bold")
        pipeline_table.add_column("Value")
        
        pipelines = result["metrics"]["pipelines"]
        pipeline_table.add_row("Total Runs", str(pipelines.get("total_runs", 0)))
        pipeline_table.add_row(
            "Success Rate",
            f"{pipelines.get('successful_runs', 0) / max(pipelines.get('total_runs', 1), 1) * 100:.1f}%"
        )
        pipeline_table.add_row(
            "Average Duration",
            f"{pipelines.get('average_duration', 0) / 60:.1f} minutes"
        )
        
        console.print(pipeline_table)
        
        # Insights
        if "insights" in result:
            console.print(Panel(
                Markdown(result["insights"]),
                title="System Insights",
                border_style="blue"
            ))
    else:
        console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")

@cli.command()
@click.argument('plugin_name')
@run_async
async def install_plugin(plugin_name):
    """Install a Jenkins plugin."""
    supervisor = SupervisorAgent()
    
    with console.status("[bold blue]Installing plugin...[/bold blue]"):
        result = await supervisor.handle_task(f"Install {plugin_name} plugin")
    
    if result["status"] == "success":
        console.print(f"[green]Successfully installed {plugin_name}[/green]")
        if "recommendations" in result:
            console.print(Panel(
                Markdown("\n".join(f"- {r}" for r in result["recommendations"])),
                title="Plugin Recommendations",
                border_style="yellow"
            ))
    else:
        console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")

@cli.command()
@run_async
async def list_plugins():
    """List installed Jenkins plugins."""
    supervisor = SupervisorAgent()
    
    with console.status("[bold blue]Getting plugins...[/bold blue]"):
        result = await supervisor.handle_task("List installed plugins")
    
    if result["status"] == "success" and "plugins" in result:
        table = Table(title="Installed Plugins")
        table.add_column("Name", style="bold")
        table.add_column("Version")
        table.add_column("Status")
        
        for plugin in result["plugins"]:
            table.add_row(
                plugin["name"],
                plugin["version"],
                plugin.get("status", "Active")
            )
        
        console.print(table)
    else:
        console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")

def main():
    """Main entry point for CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()