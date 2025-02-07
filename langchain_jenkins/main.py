"""Main entry point for the LangChain Jenkins Agent system."""
import asyncio
import argparse
from typing import Dict, Any
from agents.supervisor import SupervisorAgent
from config.config import config

async def process_task(supervisor: SupervisorAgent, task: str) -> Dict[str, Any]:
    """Process a task using the supervisor agent.
    
    Args:
        supervisor: Supervisor agent instance
        task: Task description
        
    Returns:
        Task execution results
    """
    if "complex" in task.lower():
        return await supervisor.handle_complex_task(task)
    else:
        return await supervisor.handle_task(task)

async def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="LangChain Jenkins Agent")
    parser.add_argument(
        "--task",
        type=str,
        help="Task to execute"
    )
    args = parser.parse_args()
    
    if not args.task:
        print("Please provide a task using --task")
        return
    
    # Initialize supervisor agent
    supervisor = SupervisorAgent()
    
    # Process the task
    result = await process_task(supervisor, args.task)
    
    # Print the result
    print("\nTask Result:")
    print("============")
    print(f"Task: {args.task}")
    print(f"Status: {result.get('status', 'unknown')}")
    if result.get('error'):
        print(f"Error: {result['error']}")
    if result.get('results'):
        print("\nDetailed Results:")
        for agent_type, agent_result in result['results'].items():
            print(f"\n{agent_type.upper()} Agent Results:")
            print("-" * (len(agent_type) + 14))
            for key, value in agent_result.items():
                if key != 'status':
                    print(f"{key}: {value}")

if __name__ == "__main__":
    asyncio.run(main())