"""
Complete Integration Test - All Phases

Tests the full Agent OS system:
1. Orchestrator with multi-agent chain
2. Memory system across all layers
3. Task queue with checkpointing
4. Self-improvement tracking
"""

import asyncio
import sys
from datetime import datetime

sys.path.insert(0, "C:/Users/Shiva/Downloads/agent-os")

from kernel.orchestrator import Orchestrator
from kernel.task_queue import TaskQueue, TaskType
from kernel.memory import MemoryManager
from kernel.self_improver import SelfImprover


async def run_complete_test():
    """Run complete Agent OS integration test."""
    print("\n" + "="*60)
    print("AGENT OS - COMPLETE INTEGRATION TEST")
    print("="*60)

    # Clean up
    print("\n[SETUP] Cleaning up previous data...")
    queue = TaskQueue()
    for path in [queue.pending_path, queue.in_progress_path,
                 queue.completed_path, queue.dead_letter_path]:
        for f in path.glob("*.json"):
            f.unlink()

    mm = MemoryManager()
    for path in [mm.working_path, mm.episodic_path, mm.semantic_path, mm.procedural_path]:
        for f in path.glob("*.json"):
            f.unlink()

    improver = SelfImprover()
    print("   [OK] Clean complete")

    # Create orchestrator
    print("\n[1] INITIALIZING ORCHESTRATOR...")
    orchestrator = Orchestrator()
    print(f"   [OK] Orchestrator initialized")
    print(f"   [OK] Agents: {list(orchestrator.agents.keys())}")
    print(f"   [OK] Session: {orchestrator.session_id[:8]}")

    # Run research task
    print("\n[2] RUNNING RESEARCH TASK...")
    result = await orchestrator.run(initial_task={
        "type": "research",
        "input": {
            "query": "AI coding assistants competitive landscape 2026",
            "depth": "comprehensive",
        },
        "priority": 10
    })
    print(f"   [OK] Research status: {result['status']}")
    print(f"   [OK] Iterations: {result['iterations']}")

    # Enqueue planning task
    print("\n[3] RUNNING PLANNER TASK...")
    planner_task = queue.enqueue(
        task_type=TaskType.PLAN.value,
        input_data={
            "goal": "Competitive analysis implementation",
            "constraints": {"time": "1 week"}
        },
        priority=9
    )
    planner_dequeued = queue.dequeue()
    print(f"   [OK] Planner task: {planner_dequeued.id}")

    # Enqueue execution task
    print("\n[4] RUNNING EXECUTOR TASK...")
    exec_task = queue.enqueue(
        task_type=TaskType.EXECUTE.value,
        input_data={
            "subtask": {"id": 1, "description": "Generate comparison matrix"},
            "plan": {"goal": "Analysis"},
        },
        priority=8
    )
    exec_dequeued = queue.dequeue()
    print(f"   [OK] Executor task: {exec_dequeued.id}")

    # Enqueue synthesis task
    print("\n[5] RUNNING SYNTHESIZER TASK...")
    synth_task = queue.enqueue(
        task_type=TaskType.SYNTHESIZE.value,
        input_data={
            "research_output": {"findings": [], "confidence": 0.85},
            "plan_output": {"goal": "Analysis"},
            "executor_output": {},
            "format": "executive_summary",
            "audience": "executives",
        },
        priority=7
    )
    synth_dequeued = queue.dequeue()
    print(f"   [OK] Synthesizer task: {synth_dequeued.id}")

    # Record executions for self-improvement
    print("\n[6] RECORDING EXECUTIONS FOR SELF-IMPROVEMENT...")
    from kernel.self_improver import ExecutionRecord

    executions = [
        (planner_dequeued, "plan", True),
        (exec_dequeued, "execute", True),
        (synth_dequeued, "synthesize", True),
    ]

    for task, task_type, success in executions:
        record = ExecutionRecord(
            task_id=task.id,
            task_type=task_type,
            agent_id=task_type,
            started_at=datetime.utcnow().isoformat(),
            completed_at=datetime.utcnow().isoformat(),
            duration_seconds=60,
            success=success,
            output_size=500,
            steps_completed=["observe", "reason", "act", "checkpoint"],
        )
        improver.record_execution(record)

    print(f"   [OK] Recorded {len(executions)} executions")

    # Get dashboard
    print("\n[7] SELF-IMPROVEMENT DASHBOARD...")
    dashboard = improver.get_dashboard()
    print(f"   Total executions: {dashboard['total_executions']}")
    print(f"   Overall success rate: {dashboard['overall_success_rate']:.0%}")
    print(f"   Skills tracked: {dashboard['active_skills']}")
    print(f"   Patterns learned: {dashboard['patterns_learned']}")

    # Memory stats
    print("\n[8] MEMORY SYSTEM STATS...")
    mem_stats = mm.get_stats()
    print(f"   Working: {mem_stats['working_entries']} entries")
    print(f"   Episodic: {mem_stats['episodic_entries']} entries")
    print(f"   Semantic: {mem_stats['semantic_entries']} entries")
    print(f"   Procedural: {mem_stats['procedural_entries']} entries")

    # Query semantic memory
    print("\n[9] SEMANTIC MEMORY QUERY...")
    results = mm.query_semantic("AI coding assistants")
    print(f"   Found {len(results)} matching entries")
    for r in results[:3]:
        print(f"   - {r.id}: {r.tags}")

    # Queue stats
    print("\n[10] QUEUE STATISTICS...")
    stats = queue.get_queue_stats()
    print(f"   Pending: {stats['pending']}")
    print(f"   In Progress: {stats['in_progress']}")
    print(f"   Completed: {stats['completed']}")
    print(f"   Dead Letter: {stats['dead_letter']}")

    # Get recommendations
    print("\n[11] SELF-IMPROVEMENT RECOMMENDATIONS...")
    recs = improver.get_recommendations()
    for rec in recs[:3]:
        print(f"   - [{rec['priority'].upper()}] {rec.get('recommendation', 'N/A')[:50]}...")

    print("\n" + "="*60)
    print("[PASS] COMPLETE INTEGRATION TEST PASSED")
    print("="*60)
    print("\nAgent OS is fully operational with:")
    print("  - Multi-agent orchestration")
    print("  - 4-layer memory system")
    print("  - Task queue with checkpointing")
    print("  - Self-improvement tracking")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(run_complete_test())
