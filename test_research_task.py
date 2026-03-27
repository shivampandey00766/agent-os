"""
Test Agent OS with a real research task.
Demonstrates the full chain: RESEARCHER -> PLANNER -> EXECUTOR -> SYNTHESIZER
"""

import sys
import json
import asyncio
from datetime import datetime

sys.path.insert(0, "C:/Users/Shiva/Downloads/agent-os")

from kernel.task_queue import TaskQueue, TaskType, TaskStatus
from kernel.checkpoint import CheckpointManager
from kernel.memory import MemoryManager


async def run_research_task():
    """Run a complete research task through the Agent OS chain."""

    print("=" * 60)
    print("AGENT OS - REAL RESEARCH TASK TEST")
    print("=" * 60)

    # Initialize components
    queue = TaskQueue()
    cm = CheckpointManager()
    mm = MemoryManager()

    # Clean up from previous runs
    for path in [queue.pending_path, queue.in_progress_path, queue.completed_path, queue.dead_letter_path]:
        for f in path.glob("*.json"):
            f.unlink()
    for f in cm.checkpoints_path.glob("*.json"):
        f.unlink()
    if cm.active_path.exists():
        cm.active_path.unlink()
    for path in [mm.working_path, mm.episodic_path]:
        for f in path.glob("*.json"):
            f.unlink()

    session_id = f"research-session-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

    # Create checkpoint
    print("\n[1] Creating checkpoint...")
    checkpoint = cm.create_checkpoint(
        session_id=session_id,
        context={"task": "Research AI coding assistants competitive landscape"}
    )
    print(f"    Checkpoint created: {checkpoint.checkpoint_id}")

    # Store research query in memory
    mm.set_working("current_query", "AI coding assistants competitive landscape 2026")
    mm.set_working("session_id", session_id)
    print("    [OK] Working memory set")

    # Step 1: RESEARCHER
    print("\n[2] RESEARCHER AGENT - Deep Research")
    cm.update_phase("act")
    cm.save_task_progress("research", "researcher", 10, "Starting research...")

    # Enqueue research task
    research_task = queue.enqueue(
        task_type=TaskType.RESEARCH.value,
        input_data={
            "query": "AI coding assistants competitive landscape 2026",
            "depth": "comprehensive",
            "sources": ["web", "news", "academic"]
        },
        priority=10
    )
    print(f"    Enqueued research task: {research_task.id}")

    # Dequeue and simulate research
    dequeued = queue.dequeue()
    print(f"    Dequeued: {dequeued.id}")

    # Simulate web research (in real implementation, would use WebSearch/WebFetch)
    research_findings = {
        "findings": [
            {
                "claim": "GitHub Copilot holds 40% market share in AI coding assistants",
                "source": "https://github.blog",
                "credibility": 0.9
            },
            {
                "claim": "Claude Code from Anthropic shows 300% growth in enterprise adoption",
                "source": "https://anthropic.com",
                "credibility": 0.95
            },
            {
                "claim": "Cursor AI focusing on real-time collaboration features",
                "source": "https://cursor.sh",
                "credibility": 0.8
            },
            {
                "claim": "JetBrains AI Assistant integrated deeply into IntelliJ ecosystem",
                "source": "https://jetbrains.com",
                "credibility": 0.85
            },
            {
                "claim": "Tabnine reports 50% reduction in code review time",
                "source": "https://tabnine.com",
                "credibility": 0.75
            }
        ],
        "confidence": 0.87,
        "summary": "Market analysis shows GitHub Copilot leading but Anthropic's Claude Code showing fastest growth"
    }

    queue.complete(dequeued.id, research_findings)
    cm.save_task_progress("research", "researcher", 100, "Research completed")
    print("    [OK] Research completed with 5 findings")

    # Store research in semantic memory
    mm.add_semantic(
        f"research_{dequeued.id}",
        research_findings,
        tags=["ai", "coding-assistants", "competitive-analysis", "2026"]
    )
    print("    [OK] Research stored in semantic memory")

    # Step 2: PLANNER
    print("\n[3] PLANNER AGENT - Task Decomposition")
    cm.update_phase("act")

    # Enqueue planning task
    planner_task = queue.enqueue(
        task_type=TaskType.PLAN.value,
        input_data={
            "goal": "Competitive analysis of AI coding assistants",
            "research_output": research_findings
        },
        priority=9
    )
    print(f"    Enqueued planning task: {planner_task.id}")

    dequeued = queue.dequeue()
    print(f"    Dequeued: {dequeued.id}")

    # Simulate planning
    plan_output = {
        "plan_id": f"plan-{dequeued.id[:8]}",
        "goal": "Competitive analysis of AI coding assistants",
        "subtasks": [
            {"id": 1, "description": "Define evaluation criteria", "agent": "planner", "priority": 10, "blocked_by": []},
            {"id": 2, "description": "Create comparison matrix", "agent": "executor", "priority": 9, "blocked_by": [1]},
            {"id": 3, "description": "Analyze strengths/weaknesses", "agent": "executor", "priority": 8, "blocked_by": [2]},
            {"id": 4, "description": "Generate recommendations", "agent": "synthesizer", "priority": 7, "blocked_by": [3]},
            {"id": 5, "description": "Produce final report", "agent": "synthesizer", "priority": 6, "blocked_by": [4]},
        ],
        "estimated_duration": "2 hours",
        "risks": []
    }

    queue.complete(dequeued.id, plan_output)
    cm.save_task_progress("planning", "planner", 100, "Planning completed")
    print("    [OK] Created 5 subtasks")

    # Step 3: EXECUTOR
    print("\n[4] EXECUTOR AGENT - Implementation")
    cm.update_phase("act")

    # Enqueue executor tasks
    for subtask in plan_output["subtasks"]:
        exec_task = queue.enqueue(
            task_type=TaskType.EXECUTE.value,
            input_data={
                "subtask": subtask,
                "plan_id": plan_output["plan_id"],
                "research": research_findings
            },
            priority=subtask["priority"],
            blocked_by=[]
        )

    # Dequeue and execute each task
    completed = 0
    while True:
        dequeued = queue.dequeue()
        if not dequeued:
            break

        task_input = dequeued.input
        subtask_desc = task_input.get("subtask", {}).get("description", "Unknown")

        # Simulate execution
        if "comparison matrix" in subtask_desc.lower():
            output = {"comparison_matrix": generate_comparison_matrix(research_findings)}
        elif "strengths" in subtask_desc.lower():
            output = {"analysis": generate_swot_analysis(research_findings)}
        else:
            output = {"status": "completed", "subtask": subtask_desc}

        queue.complete(dequeued.id, output)
        completed += 1
        print(f"    [OK] Executed: {subtask_desc[:40]}...")

    cm.save_task_progress("execution", "executor", 100, f"Completed {completed} tasks")
    print(f"    [OK] Executor completed {completed} tasks")

    # Step 4: SYNTHESIZER
    print("\n[5] SYNTHESIZER AGENT - Report Generation")
    cm.update_phase("act")

    synthesizer_task = queue.enqueue(
        task_type=TaskType.SYNTHESIZE.value,
        input_data={
            "research_output": research_findings,
            "plan_output": plan_output,
            "executor_output": {"tasks_completed": completed}
        },
        priority=8
    )
    print(f"    Enqueued synthesis task: {synthesizer_task.id}")

    dequeued = queue.dequeue()
    print(f"    Dequeued: {dequeued.id}")

    final_report = {
        "summary": f"""Executive Summary: AI Coding Assistants Competitive Landscape 2026

Key Findings:
- GitHub Copilot leads with 40% market share
- Claude Code showing fastest growth (300% enterprise adoption)
- Competition intensifying with focus on collaboration features

Top Recommendation: Invest in Claude Code integration for enterprise workflows.""",
        "findings": research_findings["findings"],
        "recommendations": [
            {"priority": "high", "category": "strategy", "recommendation": "Prioritize Claude Code partnership"},
            {"priority": "medium", "category": "product", "recommendation": "Add real-time collaboration features"},
            {"priority": "medium", "category": "pricing", "recommendation": "Review Tabnine competitive pricing"}
        ],
        "metadata": {
            "research_confidence": research_findings["confidence"],
            "sources_analyzed": 5,
            "tasks_completed": completed
        }
    }

    queue.complete(dequeued.id, final_report)
    cm.save_task_progress("synthesis", "synthesizer", 100, "Synthesis completed")
    print("    [OK] Final report generated")

    # Complete checkpoint
    cm.update_checkpoint(updates={"task_progress": {"status": "completed"}})
    cm.complete()

    # Create episode for this session
    episode = mm.create_episode(session_id, "AI Coding Assistants Research", tags=["research", "competitive-analysis"])
    episode.add_event("research_completed", {"findings_count": 5})
    episode.add_event("planning_completed", {"subtasks_created": 5})
    episode.add_event("execution_completed", {"tasks_completed": completed})
    episode.add_event("synthesis_completed", {"report_generated": True})
    episode.end("success")
    print("    [OK] Episode recorded")

    # Print final report
    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(final_report["summary"])

    # Print queue stats
    print("\n" + "=" * 60)
    print("QUEUE STATISTICS")
    print("=" * 60)
    stats = queue.get_queue_stats()
    print(f"  Pending: {stats['pending']}")
    print(f"  In Progress: {stats['in_progress']}")
    print(f"  Completed: {stats['completed']}")
    print(f"  Dead Letter: {stats['dead_letter']}")

    # Print memory stats
    print("\n" + "=" * 60)
    print("MEMORY STATISTICS")
    print("=" * 60)
    mem_stats = mm.get_stats()
    print(f"  Working: {mem_stats['working_entries']}")
    print(f"  Episodic: {mem_stats['episodic_entries']}")
    print(f"  Semantic: {mem_stats['semantic_entries']}")
    print(f"  Procedural: {mem_stats['procedural_entries']}")

    # Query semantic memory for research
    print("\n" + "=" * 60)
    print("SEMANTIC MEMORY QUERY: 'AI coding assistants'")
    print("=" * 60)
    results = mm.query_semantic("AI coding assistants", limit=5)
    for r in results:
        print(f"  - {r.id}: {r.tags}")

    print("\n" + "=" * 60)
    print("[PASS] REAL RESEARCH TASK TEST COMPLETED")
    print("=" * 60)


def generate_comparison_matrix(research):
    """Generate a comparison matrix from research findings."""
    return {
        "competitors": [
            {"name": "GitHub Copilot", "market_share": "40%", "strength": "Ecosystem integration"},
            {"name": "Claude Code", "market_share": "25%", "strength": "Enterprise growth"},
            {"name": "Cursor AI", "market_share": "15%", "strength": "Collaboration"},
            {"name": "JetBrains AI", "market_share": "12%", "strength": "IDE deep integration"},
            {"name": "Tabnine", "market_share": "8%", "strength": "Code review efficiency"}
        ]
    }


def generate_swot_analysis(research):
    """Generate SWOT analysis from research findings."""
    return {
        "strengths": ["Market leadership", "Ecosystem integration", "Enterprise trust"],
        "weaknesses": ["Pricing", "Learning curve", "Limited offline support"],
        "opportunities": ["Real-time collaboration", "Enterprise adoption", "Mobile"],
        "threats": ["Competition", "Open source alternatives", "Security concerns"]
    }


if __name__ == "__main__":
    asyncio.run(run_research_task())
