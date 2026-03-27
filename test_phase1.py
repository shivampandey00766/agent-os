"""
Phase 1 Verification Test

Tests the Core Kernel components:
1. Task Queue - enqueue/dequeue/complete/fail operations
2. Checkpoint - state save/restore
3. Memory System - 4-layer operations
"""

import sys
import json
from pathlib import Path

# Add agent-os to path
sys.path.insert(0, "C:/Users/Shiva/Downloads/agent-os")

from kernel.task_queue import TaskQueue, TaskType, TaskStatus
from kernel.checkpoint import CheckpointManager, AgentState
from kernel.memory import MemoryManager, MemoryLayer


def test_task_queue():
    """Test task queue operations."""
    print("\n" + "="*60)
    print("TESTING TASK QUEUE")
    print("="*60)

    # Clean up queue directories before testing
    queue = TaskQueue()
    for path in [queue.pending_path, queue.in_progress_path, queue.completed_path, queue.dead_letter_path]:
        for f in path.glob("*.json"):
            f.unlink()

    # Test 1: Enqueue
    print("\n1. Testing enqueue...")
    task = queue.enqueue(
        task_type=TaskType.RESEARCH.value,
        input_data={"query": "AI trends 2026", "depth": "comprehensive"},
        priority=8
    )
    assert task.id is not None
    assert task.status == TaskStatus.PENDING.value
    print(f"   [OK] Enqueued task: {task.id}")

    # Test 2: Dequeue
    print("\n2. Testing dequeue...")
    dequeued = queue.dequeue()
    assert dequeued is not None
    assert dequeued.id == task.id
    assert dequeued.status == TaskStatus.IN_PROGRESS.value
    assert dequeued.attempt_count == 1
    print(f"   [OK] Dequeued task: {dequeued.id}")

    # Test 3: Complete
    print("\n3. Testing complete...")
    result = queue.complete(dequeued.id, {"findings": ["AI growing", "ML adoption up"]})
    assert result is True
    completed = queue.get_task(dequeued.id)
    assert completed.status == TaskStatus.COMPLETED.value
    assert completed.output is not None
    print(f"   [OK] Completed task: {dequeued.id}")

    # Test 4: Enqueue multiple with priorities
    print("\n4. Testing priority ordering...")
    queue.enqueue(TaskType.PLAN.value, {"goal": "task b"}, priority=5)
    queue.enqueue(TaskType.EXECUTE.value, {"goal": "task a"}, priority=10)
    queue.enqueue(TaskType.SYNTHESIZE.value, {"goal": "task c"}, priority=3)

    pending = queue.get_pending_tasks()
    assert len(pending) == 3
    assert pending[0].priority == 10  # Highest priority first
    print(f"   [OK] Priority ordering correct: {pending[0].input['goal']} (pri=10) first")

    # Test 5: Dead letter handling
    print("\n5. Testing dead letter handling...")
    dl_task = queue.enqueue(
        TaskType.RESEARCH.value,
        {"query": "will fail"},
        max_attempts=2
    )
    dl_dequeued = queue.dequeue()
    queue.fail(dl_dequeued.id, "First failure - retry")
    queue.fail(dl_dequeued.id, "Second failure - dead letter")

    dl_tasks = queue.get_dead_letter_tasks()
    assert len(dl_tasks) == 1
    assert dl_tasks[0].status == TaskStatus.DEAD_LETTER.value
    print(f"   [OK] Dead letter queue working: {len(dl_tasks)} tasks")

    # Test 6: Queue stats
    print("\n6. Testing queue stats...")
    stats = queue.get_queue_stats()
    print(f"   Stats: {stats}")
    assert stats["completed"] >= 1
    assert stats["pending"] >= 0
    print(f"   [OK] Queue stats: {stats}")

    print("\n[PASS] ALL TASK QUEUE TESTS PASSED")


def test_checkpoint():
    """Test checkpoint operations."""
    print("\n" + "="*60)
    print("TESTING CHECKPOINT SYSTEM")
    print("="*60)

    # Clean up before testing
    cm = CheckpointManager()
    for f in cm.checkpoints_path.glob("*.json"):
        f.unlink()
    if cm.active_path.exists():
        cm.active_path.unlink()

    # Test 1: Create checkpoint
    print("\n1. Testing create checkpoint...")
    cp = cm.create_checkpoint(
        session_id="test-session-001",
        current_task_id="task-123",
        context={"query": "AI trends", "depth": "comprehensive"},
        memory_snapshot={"recent": ["search1", "search2"]}
    )
    assert cp.checkpoint_id is not None
    assert cp.session_id == "test-session-001"
    print(f"   [OK] Created checkpoint: {cp.checkpoint_id}")

    # Test 2: Get active checkpoint
    print("\n2. Testing get active...")
    active = cm.get_active()
    assert active is not None
    assert active.checkpoint_id == cp.checkpoint_id
    print(f"   [OK] Active checkpoint: {active.checkpoint_id}")

    # Test 3: Update phase
    print("\n3. Testing phase update...")
    cm.update_phase("reason")
    active = cm.get_active()
    assert active.current_phase == "reason"
    print(f"   [OK] Phase updated to: {active.current_phase}")

    # Test 4: Save task progress
    print("\n4. Testing task progress...")
    cm.save_task_progress(
        task_id="task-123",
        agent_id="researcher-1",
        progress_percent=50,
        current_step="Extracting search results",
        steps_completed=["Query analysis", "Search execution"]
    )
    progress = cm.get_task_progress("task-123")
    assert progress is not None
    assert progress.progress_percent == 50
    print(f"   [OK] Task progress saved: {progress.progress_percent}%")

    # Test 5: Complete checkpoint
    print("\n5. Testing complete...")
    result = cm.complete()
    assert result is True
    active = cm.get_active()
    assert active is None  # Cleared after completion
    print(f"   [OK] Checkpoint completed")

    # Test 6: List checkpoints
    print("\n6. Testing list checkpoints...")
    checkpoints = cm.list_checkpoints("test-session-001")
    assert len(checkpoints) >= 1
    print(f"   [OK] Found {len(checkpoints)} checkpoint(s)")

    print("\n[PASS] ALL CHECKPOINT TESTS PASSED")


def test_memory():
    """Test 4-layer memory system."""
    print("\n" + "="*60)
    print("TESTING MEMORY SYSTEM")
    print("="*60)

    # Clean up before testing
    mm = MemoryManager()
    for path in [mm.working_path, mm.episodic_path, mm.semantic_path, mm.procedural_path]:
        for f in path.glob("*.json"):
            f.unlink()

    # Test 1: Working memory
    print("\n1. Testing working memory...")
    mm.set_working("current_task", {"query": "AI trends 2026", "status": "in_progress"})
    value = mm.get_working("current_task")
    assert value is not None
    assert value["query"] == "AI trends 2026"
    print(f"   [OK] Working memory: {value}")

    # Test 2: Semantic memory
    print("\n2. Testing semantic memory...")
    mm.add_semantic(
        "ai_trends_2026",
        {"summary": "Key AI trends in 2026", "findings": ["LLM improvements", "AI agents"]},
        tags=["ai", "trends", "2026"],
        importance=8
    )
    results = mm.query_semantic("AI trends")
    assert len(results) >= 1
    print(f"   [OK] Semantic query returned {len(results)} results")

    # Test 3: Procedural memory
    print("\n3. Testing procedural memory...")
    mm.add_procedural(
        "web_research",
        {"steps": ["search", "fetch", "extract"]},
        "research",
        success_rate=0.95
    )
    skill = mm.get_procedural("web_research")
    assert skill is not None
    assert skill.content["success_rate"] == 0.95
    print(f"   [OK] Procedural memory: {skill.id} (rate: {skill.content['success_rate']})")

    # Test 4: Episode creation
    print("\n4. Testing episodic memory...")
    ep = mm.create_episode("session-001", "Research AI trends", tags=["research"])
    mm.add_to_episode(ep.id, "task_start", {"task": "research"})
    mm.add_to_episode(ep.id, "task_complete", {"results": "found 10 sources"})
    mm.end_episode(ep.id, "success")

    retrieved_ep = mm.get_episode(ep.id)
    assert retrieved_ep is not None
    assert retrieved_ep.outcome == "success"
    assert len(retrieved_ep.events) == 2
    print(f"   [OK] Episode: {len(retrieved_ep.events)} events, outcome: {retrieved_ep.outcome}")

    # Test 5: Query similar across layers
    print("\n5. Testing cross-layer query...")
    similar = mm.query_similar("AI trends")
    assert "semantic" in similar
    assert "episodes" in similar
    print(f"   [OK] Cross-layer query returned semantic={len(similar['semantic'])}, episodes={len(similar['episodes'])}")

    # Test 6: Memory stats
    print("\n6. Testing memory stats...")
    stats = mm.get_stats()
    print(f"   Stats: {stats}")
    assert stats["working_entries"] >= 1
    assert stats["semantic_entries"] >= 1
    print(f"   [OK] Memory stats retrieved")

    print("\n[PASS] ALL MEMORY SYSTEM TESTS PASSED")


def test_integration():
    """Test integration between components."""
    print("\n" + "="*60)
    print("TESTING INTEGRATION")
    print("="*60)

    # Create fresh instances with cleanup
    queue = TaskQueue()
    for path in [queue.pending_path, queue.in_progress_path, queue.completed_path, queue.dead_letter_path]:
        for f in path.glob("*.json"):
            f.unlink()

    cm = CheckpointManager()
    for f in cm.checkpoints_path.glob("*.json"):
        f.unlink()
    if cm.active_path.exists():
        cm.active_path.unlink()

    mm = MemoryManager()
    for path in [mm.working_path, mm.episodic_path, mm.semantic_path, mm.procedural_path]:
        for f in path.glob("*.json"):
            f.unlink()

    # Test: Task with checkpoint and memory
    print("\n1. Testing task with checkpoint and memory...")

    # Create checkpoint
    session_id = "integration-test-001"
    cm.create_checkpoint(session_id=session_id)

    # Enqueue task
    task = queue.enqueue(
        TaskType.RESEARCH.value,
        {"query": "competitive AI landscape"},
        priority=9
    )

    # Update checkpoint with task
    cm.update_checkpoint(updates={"current_task_id": task.id})
    cm.save_task_progress(task.id, "researcher", 25, "Starting research")

    # Store in memory
    mm.set_working("current_task_id", task.id)
    mm.add_semantic(
        f"research_{task.id}",
        {"task_id": task.id, "query": "competitive AI landscape"},
        tags=["research", "ai"]
    )

    # Dequeue and complete
    dequeued = queue.dequeue()
    cm.save_task_progress(dequeued.id, "researcher", 75, "Gathering sources")
    result = queue.complete(dequeued.id, {"findings": ["Claude", "GPT-4", "Gemini"]})

    # Update memory with results
    mm.add_semantic(
        f"findings_{dequeued.id}",
        {"task_id": dequeued.id, "findings": ["Claude", "GPT-4", "Gemini"]},
        tags=["findings", "ai", "competitors"]
    )

    # End episode
    ep = mm.create_episode(session_id, "Integration test research")
    ep.add_event("task_created", {"task_id": task.id})
    ep.add_event("task_completed", {"task_id": dequeued.id, "findings_count": 3})
    ep.end("success")

    # Verify
    assert queue.get_task(dequeued.id).status == TaskStatus.COMPLETED.value
    progress = cm.get_task_progress(dequeued.id)
    assert progress.progress_percent == 75
    query_results = mm.query_semantic("competitors")
    assert len(query_results) >= 1

    print("   [OK] Task created, executed, and completed")
    print("   [OK] Checkpoint saved progress at each step")
    print("   [OK] Memory stored task context and findings")
    print("   [OK] Episode recorded full interaction")

    print("\n[PASS] ALL INTEGRATION TESTS PASSED")


def main():
    """Run all Phase 1 verification tests."""
    print("\n" + "="*60)
    print("AGENT OS - PHASE 1 VERIFICATION")
    print("="*60)

    try:
        test_task_queue()
        test_checkpoint()
        test_memory()
        test_integration()

        print("\n" + "="*60)
        print("[PASS] PHASE 1 VERIFICATION: ALL TESTS PASSED")
        print("="*60)
        return 0

    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n[FAIL] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
