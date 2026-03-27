"""
Agent OS CLI - Command-line interface for the Agent OS.
"""

import asyncio
import sys
import argparse
from datetime import datetime

from kernel.orchestrator import Orchestrator
from kernel.task_queue import TaskQueue, TaskType


def print_banner():
    """Print the Agent OS banner."""
    print("""
=================================================================
                    AGENT OS v1.0
          Deep Research Autonomous Agent System
=================================================================
""")


async def research_command(query: str, depth: str = "comprehensive"):
    """Run a research task."""
    print(f"\n[CLI] Starting research: {query}")
    print(f"[CLI] Depth: {depth}")

    orchestrator = Orchestrator()
    result = await orchestrator.run(initial_task={
        "type": "research",
        "input": {
            "query": query,
            "depth": depth,
        },
        "priority": 10
    })

    print(f"\n[CLI] Research complete!")
    print(f"       Status: {result['status']}")
    print(f"       Iterations: {result['iterations']}")

    return result


def status_command():
    """Show Agent OS status."""
    queue = TaskQueue()
    stats = queue.get_queue_stats()

    print(f"""
=================================================================
                       STATUS
=================================================================
  Queue Statistics:
    Pending:     {stats['pending']:>5}
    In Progress: {stats['in_progress']:>5}
    Completed:   {stats['completed']:>5}
    Dead Letter: {stats['dead_letter']:>5}
=================================================================
""")


def enqueue_command(task_type: str, input_data: dict, priority: int = 5):
    """Enqueue a new task."""
    queue = TaskQueue()

    type_map = {
        "research": TaskType.RESEARCH,
        "plan": TaskType.PLAN,
        "execute": TaskType.EXECUTE,
        "synthesize": TaskType.SYNTHESIZE,
    }

    task_type_enum = type_map.get(task_type, TaskType.RESEARCH)

    task = queue.enqueue(
        task_type=task_type_enum.value,
        input_data=input_data,
        priority=priority
    )

    print(f"\n[CLI] Enqueued task: {task.id}")
    print(f"       Type: {task.type}")
    print(f"       Priority: {task.priority}")

    return task


async def run_command():
    """Run the orchestrator to process queued tasks."""
    orchestrator = Orchestrator()
    result = await orchestrator.run()

    print(f"\n[CLI] Run complete!")
    print(f"       Status: {result['status']}")
    print(f"       Iterations: {result['iterations']}")

    return result


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Agent OS - Deep Research Autonomous Agent System")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Research command
    research_parser = subparsers.add_parser("research", help="Run a research task")
    research_parser.add_argument("query", help="Research query")
    research_parser.add_argument("--depth", default="comprehensive",
                                 choices=["standard", "comprehensive"],
                                 help="Research depth")

    # Status command
    subparsers.add_parser("status", help="Show Agent OS status")

    # Enqueue command
    enqueue_parser = subparsers.add_parser("enqueue", help="Enqueue a task")
    enqueue_parser.add_argument("type", choices=["research", "plan", "execute", "synthesize"],
                                help="Task type")
    enqueue_parser.add_argument("--query", help="Query for research tasks")
    enqueue_parser.add_argument("--goal", help="Goal for planning tasks")
    enqueue_parser.add_argument("--priority", type=int, default=5, help="Task priority (1-10)")

    # Run command
    subparsers.add_parser("run", help="Run the orchestrator to process queued tasks")

    args = parser.parse_args()

    print_banner()

    if not args.command:
        parser.print_help()
        return

    if args.command == "research":
        asyncio.run(research_command(args.query, args.depth))

    elif args.command == "status":
        status_command()

    elif args.command == "enqueue":
        input_data = {}
        if args.query:
            input_data["query"] = args.query
        if args.goal:
            input_data["goal"] = args.goal

        enqueue_command(args.type, input_data, args.priority)

    elif args.command == "run":
        asyncio.run(run_command())


if __name__ == "__main__":
    main()
