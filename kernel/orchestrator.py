"""
Agent OS Orchestrator - Main agent loop implementation.
Runs OBSERVE → REASON → ACT → CHECKPOINT until task completion.
"""

import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List

from kernel.task_queue import TaskQueue, TaskType, TaskStatus
from kernel.checkpoint import CheckpointManager
from kernel.memory import MemoryManager
from kernel.self_improver import SelfImprover, ExecutionRecord


class OrchestratorConfig:
    """Configuration for the orchestrator."""
    def __init__(self,
                 queue_path: str = "C:/Users/Shiva/Downloads/agent-os/queue",
                 checkpoint_path: str = "C:/Users/Shiva/Downloads/agent-os/memory/working",
                 memory_path: str = "C:/Users/Shiva/Downloads/agent-os/memory",
                 max_iterations: int = 100):
        self.queue_path = queue_path
        self.checkpoint_path = checkpoint_path
        self.memory_path = memory_path
        self.max_iterations = max_iterations


class Orchestrator:
    """
    Main agent loop orchestrator.

    Runs OBSERVE → REASON → ACT → CHECKPOINT until task completion.

    Agent Types:
    - researcher: Deep web research
    - planner: Task decomposition
    - executor: Code implementation
    - synthesizer: Result aggregation
    """

    def __init__(self, config: OrchestratorConfig = None):
        self.config = config or OrchestratorConfig()

        # Initialize kernel components
        self.task_queue = TaskQueue(self.config.queue_path)
        self.checkpoint_manager = CheckpointManager(self.config.checkpoint_path)
        self.memory = MemoryManager(self.config.memory_path)
        self.self_improver = SelfImprover(
            base_path=f"{self.config.memory_path}/procedural"
        )

        # Agent registry
        self.agents: Dict[str, Any] = {}
        self._register_agents()

        # Session state
        self.session_id = str(uuid.uuid4())
        self.current_phase = "observe"
        self.iteration = 0

    def _register_agents(self):
        """Register available agents."""
        # Import agents lazily to avoid circular dependencies
        try:
            from agents.researcher.researcher_agent import ResearcherAgent
            self.agents["researcher"] = ResearcherAgent()
        except ImportError as e:
            print(f"Warning: Could not load researcher agent: {e}")

        try:
            from agents.planner.planner_agent import PlannerAgent
            self.agents["planner"] = PlannerAgent()
        except ImportError as e:
            print(f"Warning: Could not load planner agent: {e}")

        try:
            from agents.executor.executor_agent import ExecutorAgent
            self.agents["executor"] = ExecutorAgent()
        except ImportError as e:
            print(f"Warning: Could not load executor agent: {e}")

        try:
            from agents.synthesizer.synthesizer_agent import SynthesizerAgent
            self.agents["synthesizer"] = SynthesizerAgent()
        except ImportError as e:
            print(f"Warning: Could not load synthesizer agent: {e}")

    async def run(self, initial_task: dict = None) -> dict:
        """
        Main orchestrator loop.

        Args:
            initial_task: Optional initial task dict with 'type' and 'input'

        Returns:
            {"status": "completed", "iterations": N, "result": {...}}
        """
        print(f"\n{'='*60}")
        print(f"AGENT OS ORCHESTRATOR - Session {self.session_id[:8]}")
        print(f"{'='*60}")

        # Create initial checkpoint
        self.checkpoint_manager.create_checkpoint(
            session_id=self.session_id,
            current_task_id=initial_task.get("id") if initial_task else None
        )

        # Store session in working memory
        self.memory.set_working("session_id", self.session_id)
        self.memory.set_working("started_at", datetime.utcnow().isoformat())

        # Create episode for this session
        episode = self.memory.create_episode(
            self.session_id,
            f"Agent OS session for task: {initial_task.get('type', 'unknown') if initial_task else 'dequeue'}",
            tags=["agent-os", "session"]
        )

        # If no initial task, try to dequeue one
        task = None
        if initial_task:
            task = self.task_queue.enqueue(
                task_type=initial_task.get("type", "research"),
                input_data=initial_task.get("input", {}),
                priority=initial_task.get("priority", 5)
            )
            print(f"\n[ORCHESTRATOR] Enqueued initial task: {task.id}")
        else:
            task = self.task_queue.dequeue()
            if task:
                print(f"\n[ORCHESTRATOR] Dequeued task: {task.id}")

        max_iters = self.config.max_iterations
        self.iteration = 0

        while task and self.iteration < max_iters:
            self.iteration += 1
            print(f"\n--- Iteration {self.iteration} ---")

            # OBSERVE
            await self._observe(task)
            self.checkpoint_manager.update_phase("observe")

            # REASON
            plan = await self._reason(task)
            self.checkpoint_manager.update_phase("reason")

            # ACT
            result = await self._act(task, plan)
            self.checkpoint_manager.update_phase("act")

            # CHECKPOINT
            await self._checkpoint(task, result)

            # Record execution for self-improvement
            self._record_execution(task, result)

            # Add event to episode
            episode.add_event("task_processed", {
                "task_id": task.id,
                "task_type": task.type,
                "result_status": "complete" if result.get("complete") else "failed"
            })

            # Check if task is complete
            if result.get("complete"):
                print(f"\n[ORCHESTRATOR] Task {task.id} completed successfully")
                self.task_queue.complete(task.id, result.get("output", {}))
                break

            # Handle failure
            if result.get("failed"):
                print(f"\n[ORCHESTRATOR] Task {task.id} failed: {result.get('error')}")
                self.task_queue.fail(task.id, result.get("error", "Unknown error"))
                break

            # Get next task
            task = self.task_queue.dequeue()

        # End episode
        outcome = "success" if result.get("complete") else "failed" if result.get("failed") else "incomplete"
        self.memory.end_episode(episode.id, outcome)

        # Complete checkpoint
        self.checkpoint_manager.complete()

        # Get final stats
        stats = {
            "session_id": self.session_id,
            "iterations": self.iteration,
            "status": outcome,
            "queue_stats": self.task_queue.get_queue_stats(),
            "memory_stats": self.memory.get_stats(),
        }

        print(f"\n{'='*60}")
        print(f"ORCHESTRATOR COMPLETE")
        print(f"{'='*60}")
        print(f"  Session: {self.session_id[:8]}")
        print(f"  Iterations: {self.iteration}")
        print(f"  Status: {outcome}")
        print(f"  Tasks: {stats['queue_stats']}")
        print(f"{'='*60}\n")

        return {"status": outcome, "iterations": self.iteration, "result": result}

    async def _observe(self, task) -> dict:
        """Observe current state for the task."""
        print(f"[OBSERVE] Task: {task.type} | Priority: {task.priority}")

        state = {
            "task": task,
            "context": self.memory.get_working_context(),
            "queue_depth": self.task_queue.get_queue_stats(),
        }

        # Query similar past tasks
        if task.input:
            query = task.input.get("query", "") or task.input.get("goal", "")
            if query:
                similar = self.memory.query_similar(query)
                state["similar_past"] = similar

        return state

    async def _reason(self, task) -> dict:
        """Reason about how to handle the task."""
        agent_type = task.type

        print(f"[REASON] Agent: {agent_type}")
        print(f"[REASON] Attempt: {task.attempt_count}/{task.max_attempts}")

        # Determine action plan based on task type
        steps = self._decompose_task(task, agent_type)

        plan = {
            "agent": agent_type,
            "steps": steps,
            "confidence": 0.85,
            "expected_duration": "5-10 minutes",
        }

        print(f"[REASON] Plan: {len(steps)} steps")
        for step in steps[:3]:
            print(f"  - {step}")

        return plan

    async def _act(self, task, plan: dict) -> dict:
        """Execute the planned actions."""
        agent_type = task.type
        agent = self.agents.get(agent_type)

        if not agent:
            # Fallback to generic execution if agent not loaded
            print(f"[ACT] No specific agent for {agent_type}, using generic")
            return await self._generic_act(task)

        try:
            print(f"[ACT] Executing with {agent_type} agent...")

            # Check if agent has async execute method
            if hasattr(agent, 'execute'):
                result = await agent.execute(task.input, context={"plan": plan})
            else:
                result = agent.execute(task.input, context={"plan": plan})

            return {
                "complete": True,
                "output": result,
            }

        except Exception as e:
            print(f"[ACT] Error: {e}")
            return {
                "failed": True,
                "error": str(e),
            }

    async def _generic_act(self, task) -> dict:
        """Generic action execution when no specific agent is available."""
        print(f"[ACT] Generic execution for {task.type}")

        # Simulate some processing
        await asyncio.sleep(0.1)

        return {
            "complete": True,
            "output": {
                "status": "generic_execution",
                "task_type": task.type,
                "input": task.input,
            },
        }

    async def _checkpoint(self, task, result: dict):
        """Save checkpoint with current progress."""
        self.checkpoint_manager.update_checkpoint(
            updates={
                "current_task_id": task.id,
                "current_phase": self.current_phase,
                "task_progress": {
                    "status": "completed" if result.get("complete") else "failed",
                    "iteration": self.iteration,
                }
            }
        )

        # Update task progress
        progress_percent = 100 if result.get("complete") else (
            50 if result.get("partial") else 0
        )
        self.checkpoint_manager.save_task_progress(
            task_id=task.id,
            agent_id=task.type,
            progress_percent=progress_percent,
            current_step="completed" if result.get("complete") else "failed",
            steps_completed=["observe", "reason", "act", "checkpoint"] if result.get("complete") else []
        )

    def _record_execution(self, task, result: dict):
        """Record execution for self-improvement analysis."""
        record = ExecutionRecord(
            task_id=task.id,
            task_type=task.type,
            agent_id=task.type,
            started_at=datetime.utcnow().isoformat(),
            completed_at=datetime.utcnow().isoformat(),
            duration_seconds=1,  # Simplified
            success=result.get("complete", False),
            error=result.get("error"),
            output_size=len(str(result.get("output", {}))),
            steps_completed=["observe", "reason", "act", "checkpoint"]
        )

        self.self_improver.record_execution(record)

    def _decompose_task(self, task, agent_type: str) -> list:
        """Decompose task into steps based on agent type."""
        decompositions = {
            "research": [
                "Analyze query and formulate search strategy",
                "Execute parallel web searches",
                "Extract and validate content from sources",
                "Synthesize findings with confidence scoring",
            ],
            "plan": [
                "Understand end goal from research",
                "Identify dependencies and constraints",
                "Break down into ordered subtasks",
                "Assign priorities and resources",
            ],
            "execute": [
                "Review implementation plan",
                "Set up development environment",
                "Implement code/features",
                "Run tests and validate",
            ],
            "synthesize": [
                "Gather outputs from all agents",
                "Identify key insights and patterns",
                "Structure final deliverable",
                "Add executive summary and recommendations",
            ],
        }
        return decompositions.get(agent_type, ["Generic task step"])


async def run_research_task(query: str, depth: str = "comprehensive"):
    """Convenience function to run a research task through the orchestrator."""
    orchestrator = Orchestrator()

    result = await orchestrator.run(initial_task={
        "type": "research",
        "input": {
            "query": query,
            "depth": depth,
        },
        "priority": 10
    })

    return result


if __name__ == "__main__":
    # Test the orchestrator
    async def test():
        result = await run_research_task("AI coding assistants competitive landscape 2026")
        print(f"\nFinal result: {result}")

    asyncio.run(test())
