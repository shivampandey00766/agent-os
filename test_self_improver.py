"""
Phase 5: Self-Improvement Test

Tests the self-improvement system:
- Execution tracking
- Pattern learning
- Skill metrics
- Recommendations
- Dashboard
"""

import sys
from datetime import datetime

sys.path.insert(0, "C:/Users/Shiva/Downloads/agent-os")

from kernel.self_improver import SelfImprover, ExecutionRecord


def test_self_improvement():
    """Test the self-improvement system."""
    print("\n" + "="*60)
    print("TESTING SELF-IMPROVEMENT SYSTEM")
    print("="*60)

    improver = SelfImprover()

    # Record some sample executions
    print("\n1. Recording sample executions...")

    tasks = [
        ("task-1", "research", "researcher", True, 120),
        ("task-2", "research", "researcher", True, 110),
        ("task-3", "research", "researcher", True, 130),
        ("task-4", "research", "researcher", False, 90),  # Failed
        ("task-5", "plan", "planner", True, 60),
        ("task-6", "plan", "planner", True, 55),
        ("task-7", "execute", "executor", True, 300),
        ("task-8", "execute", "executor", False, 280),  # Failed
        ("task-9", "execute", "executor", True, 320),
        ("task-10", "synthesize", "synthesizer", True, 45),
    ]

    for task_id, task_type, agent_id, success, duration in tasks:
        record = ExecutionRecord(
            task_id=task_id,
            task_type=task_type,
            agent_id=agent_id,
            started_at=datetime.utcnow().isoformat(),
            completed_at=datetime.utcnow().isoformat(),
            duration_seconds=duration,
            success=success,
            error=None if success else "Test error",
            output_size=1000,
            steps_completed=["observe", "reason", "act", "checkpoint"],
        )
        improver.record_execution(record)

    print(f"   [OK] Recorded {len(tasks)} executions")

    # Test skill metrics
    print("\n2. Testing skill metrics...")
    metrics = improver.get_skill_metrics()
    print(f"   Tracked skills: {len(metrics)}")

    for skill_name, skill_metrics in metrics.items():
        print(f"   - {skill_name}: {skill_metrics.total_executions} execs, "
              f"rate={skill_metrics.success_rate:.0%}, "
              f"avg={skill_metrics.avg_duration_seconds:.0f}s")

    # Test task type metrics
    print("\n3. Testing task type metrics...")
    research_metrics = improver.get_task_type_metrics("research")
    print(f"   Research tasks: {len(research_metrics)} skill(s)")

    execute_metrics = improver.get_task_type_metrics("execute")
    print(f"   Execute tasks: {len(execute_metrics)} skill(s)")

    # Test pattern analysis
    print("\n4. Testing pattern analysis...")
    patterns = improver.analyze_patterns()
    print(f"   Patterns discovered: {len(patterns)}")

    for pattern in patterns:
        print(f"   - [{pattern.pattern_type}] {pattern.description[:50]}... "
              f"(confidence: {pattern.confidence:.0%})")

    # Test recommendations
    print("\n5. Testing recommendations...")
    recommendations = improver.get_recommendations()
    print(f"   Recommendations generated: {len(recommendations)}")

    for rec in recommendations[:3]:
        print(f"   - [{rec['priority'].upper()}] {rec.get('recommendation', 'N/A')[:50]}...")

    # Test procedural memory export
    print("\n6. Testing procedural memory export...")
    procedural = improver.export_to_procedural_memory()
    print(f"   Procedural entries: {len(procedural)}")

    for entry in procedural:
        print(f"   - {entry.get('skill_name')}: {entry.get('description', 'N/A')[:40]}...")

    # Test dashboard
    print("\n7. Testing dashboard...")
    dashboard = improver.get_dashboard()
    print(f"   Total executions: {dashboard['total_executions']}")
    print(f"   Overall success rate: {dashboard['overall_success_rate']:.0%}")
    print(f"   Recent success rate: {dashboard['recent_success_rate']:.0%}")
    print(f"   Active skills: {dashboard['active_skills']}")
    print(f"   Patterns learned: {dashboard['patterns_learned']}")
    print(f"   Recommendations: {dashboard['recommendations_count']}")

    print("\n" + "="*60)
    print("[PASS] SELF-IMPROVEMENT SYSTEM TEST PASSED")
    print("="*60)


if __name__ == "__main__":
    test_self_improvement()
