"""
Self-Improver - Learning from execution feedback

Analyzes task execution to improve future performance:
- Track success rate, execution time per task type
- Extract successful patterns → procedural memory
- Improve skills based on failure analysis
- Quality metrics dashboard
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict, field
from collections import defaultdict


@dataclass
class ExecutionRecord:
    """Record of a single task execution."""
    task_id: str
    task_type: str
    agent_id: str
    started_at: str
    completed_at: Optional[str] = None
    duration_seconds: int = 0
    success: bool = False
    error: Optional[str] = None
    output_size: int = 0
    steps_completed: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ExecutionRecord":
        return cls(**data)


@dataclass
class SkillMetrics:
    """Metrics for a specific skill."""
    skill_name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_duration_seconds: int = 0
    avg_duration_seconds: float = 0
    avg_output_size: float = 0
    last_executed_at: Optional[str] = None
    success_rate: float = 1.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SkillMetrics":
        return cls(**data)


@dataclass
class Pattern:
    """A learned pattern from execution history."""
    pattern_id: str
    pattern_type: str  # "success", "failure", "optimization"
    description: str
    evidence: list = field(default_factory=list)  # Task IDs that support this pattern
    success_count: int = 0
    failure_count: int = 0
    confidence: float = 0.5
    created_at: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Pattern":
        return cls(**data)


class SelfImprover:
    """
    Analyzes execution history to improve future performance.

    Features:
    - Track metrics per task type and agent
    - Identify success/failure patterns
    - Generate improvement recommendations
    - Update procedural memory with learned patterns
    """

    def __init__(
        self,
        base_path: str = "C:/Users/Shiva/Downloads/agent-os/memory/procedural"
    ):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        self.execution_log_path = self.base_path / "execution_log.json"
        self.metrics_path = self.base_path / "skill_metrics.json"
        self.patterns_path = self.base_path / "learned_patterns.json"

        # Load or initialize
        self.execution_records: List[ExecutionRecord] = self._load_records()
        self.skill_metrics: Dict[str, SkillMetrics] = self._load_metrics()
        self.patterns: List[Pattern] = self._load_patterns()

    # ========== Record Keeping ==========

    def record_execution(self, record: ExecutionRecord) -> None:
        """Record a task execution for analysis."""
        self.execution_records.append(record)
        self._save_records()

        # Update metrics
        self._update_skill_metrics(record)

    def _load_records(self) -> List[ExecutionRecord]:
        """Load execution records from disk."""
        if self.execution_log_path.exists():
            with open(self.execution_log_path, 'r') as f:
                data = json.load(f)
                return [ExecutionRecord.from_dict(r) for r in data]
        return []

    def _save_records(self) -> None:
        """Save execution records to disk."""
        # Keep only last 1000 records to prevent unbounded growth
        records = self.execution_records[-1000:]
        with open(self.execution_log_path, 'w') as f:
            json.dump([r.to_dict() for r in records], f, indent=2)
        self.execution_records = records

    def _load_metrics(self) -> Dict[str, SkillMetrics]:
        """Load skill metrics from disk."""
        if self.metrics_path.exists():
            with open(self.metrics_path, 'r') as f:
                data = json.load(f)
                return {k: SkillMetrics.from_dict(v) for k, v in data.items()}
        return {}

    def _save_metrics(self) -> None:
        """Save skill metrics to disk."""
        with open(self.metrics_path, 'w') as f:
            json.dump({k: v.to_dict() for k, v in self.skill_metrics.items()}, f, indent=2)

    def _load_patterns(self) -> List[Pattern]:
        """Load learned patterns from disk."""
        if self.patterns_path.exists():
            with open(self.patterns_path, 'r') as f:
                data = json.load(f)
                return [Pattern.from_dict(p) for p in data]
        return []

    def _save_patterns(self) -> None:
        """Save learned patterns to disk."""
        with open(self.patterns_path, 'w') as f:
            json.dump([p.to_dict() for p in self.patterns], f, indent=2)

    # ========== Metrics Analysis ==========

    def _update_skill_metrics(self, record: ExecutionRecord) -> None:
        """Update metrics for a skill after execution."""
        skill_name = f"{record.agent_id}_{record.task_type}"

        if skill_name not in self.skill_metrics:
            self.skill_metrics[skill_name] = SkillMetrics(skill_name=skill_name)

        metrics = self.skill_metrics[skill_name]
        metrics.total_executions += 1
        metrics.total_duration_seconds += record.duration_seconds

        if record.success:
            metrics.successful_executions += 1
        else:
            metrics.failed_executions += 1

        metrics.success_rate = metrics.successful_executions / metrics.total_executions
        metrics.avg_duration_seconds = metrics.total_duration_seconds / metrics.total_executions
        metrics.avg_output_size = sum(
            r.output_size for r in self.execution_records[-100:]
            if r.agent_id == record.agent_id and r.task_type == record.task_type
        ) / min(100, metrics.total_executions)

        metrics.last_executed_at = datetime.utcnow().isoformat()

        self._save_metrics()

    def get_skill_metrics(self, skill_name: str = None) -> Dict[str, SkillMetrics]:
        """Get metrics for a specific skill or all skills."""
        if skill_name:
            return {skill_name: self.skill_metrics.get(skill_name)} if skill_name in self.skill_metrics else {}
        return self.skill_metrics

    def get_task_type_metrics(self, task_type: str) -> Dict[str, SkillMetrics]:
        """Get metrics for all agents on a specific task type."""
        return {
            k: v for k, v in self.skill_metrics.items()
            if k.endswith(f"_{task_type}")
        }

    # ========== Pattern Learning ==========

    def analyze_patterns(self) -> List[Pattern]:
        """Analyze execution history to identify patterns."""
        # Group by task type
        by_type = defaultdict(list)
        for record in self.execution_records[-100:]:
            by_type[record.task_type].append(record)

        # Analyze each task type
        for task_type, records in by_type.items():
            successful = [r for r in records if r.success]
            failed = [r for r in records if not r.success]

            if len(successful) >= 3:
                # Look for success patterns
                success_pattern = self._extract_success_pattern(task_type, successful)
                if success_pattern:
                    self.patterns.append(success_pattern)

            if len(failed) >= 2:
                # Look for failure patterns
                failure_pattern = self._extract_failure_pattern(task_type, failed)
                if failure_pattern:
                    self.patterns.append(failure_pattern)

        # Deduplicate and update confidence
        self.patterns = self._deduplicate_patterns()
        self._update_pattern_confidence()
        self._save_patterns()

        return self.patterns

    def _extract_success_pattern(self, task_type: str, records: List[ExecutionRecord]) -> Optional[Pattern]:
        """Extract pattern from successful executions."""
        if not records:
            return None

        # Calculate average metrics
        avg_duration = sum(r.duration_seconds for r in records) / len(records)
        common_steps = self._find_common_steps(records)

        if common_steps:
            pattern = Pattern(
                pattern_id=f"success_{task_type}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                pattern_type="success",
                description=f"Successful {task_type} tasks complete in ~{avg_duration:.0f}s with steps: {', '.join(common_steps[:3])}",
                evidence=[r.task_id for r in records[-5:]],
                success_count=len(records),
                confidence=min(0.95, 0.5 + (len(records) * 0.05)),
            )
            return pattern

        return None

    def _extract_failure_pattern(self, task_type: str, records: List[ExecutionRecord]) -> Optional[Pattern]:
        """Extract pattern from failed executions."""
        if not records:
            return None

        # Find common errors
        common_errors = self._find_common_errors(records)

        if common_errors:
            pattern = Pattern(
                pattern_id=f"failure_{task_type}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                pattern_type="failure",
                description=f"Failed {task_type} tasks often have: {common_errors[0]}",
                evidence=[r.task_id for r in records[-5:]],
                failure_count=len(records),
                confidence=min(0.9, 0.3 + (len(records) * 0.1)),
            )
            return pattern

        return None

    def _find_common_steps(self, records: List[ExecutionRecord]) -> list:
        """Find steps common across records."""
        if not records:
            return []

        step_counts = defaultdict(int)
        for record in records:
            for step in record.steps_completed:
                step_counts[step] += 1

        # Return steps that appear in >50% of records
        threshold = len(records) * 0.5
        return [step for step, count in step_counts.items() if count >= threshold]

    def _find_common_errors(self, records: List[ExecutionRecord]) -> list:
        """Find common errors across records."""
        error_counts = defaultdict(int)
        for record in records:
            if record.error:
                # Normalize error (take first sentence)
                error_key = record.error.split('.')[0][:50]
                error_counts[error_key] += 1

        # Return errors that appear >50%
        threshold = len(records) * 0.5
        return [error for error, count in error_counts.items() if count >= threshold]

    def _deduplicate_patterns(self) -> List[Pattern]:
        """Remove duplicate patterns."""
        seen = {}
        unique = []

        for pattern in self.patterns:
            key = pattern.description[:50]  # Dedupe by first 50 chars
            if key not in seen:
                seen[key] = pattern
                unique.append(pattern)
            else:
                # Merge evidence
                existing = seen[key]
                existing.evidence.extend(pattern.evidence)
                existing.success_count += pattern.success_count
                existing.failure_count += pattern.failure_count

        return unique

    def _update_pattern_confidence(self) -> None:
        """Update confidence scores based on evidence."""
        for pattern in self.patterns:
            total = pattern.success_count + pattern.failure_count
            if total > 0:
                if pattern.pattern_type == "success":
                    pattern.confidence = pattern.success_count / total
                else:
                    pattern.confidence = pattern.failure_count / total

    # ========== Recommendations ==========

    def get_recommendations(self) -> List[dict]:
        """Generate improvement recommendations based on analysis."""
        recommendations = []

        # Based on skill metrics
        for skill_name, metrics in self.skill_metrics.items():
            if metrics.success_rate < 0.7:
                recommendations.append({
                    "type": "skill_improvement",
                    "priority": "high",
                    "skill": skill_name,
                    "issue": f"Low success rate: {metrics.success_rate:.0%}",
                    "recommendation": f"Review and improve {skill_name} implementation",
                    "evidence": f"Failed {metrics.failed_executions} of {metrics.total_executions} executions",
                })

            if metrics.avg_duration_seconds > 600:  # > 10 minutes
                recommendations.append({
                    "type": "optimization",
                    "priority": "medium",
                    "skill": skill_name,
                    "issue": f"Long execution time: {metrics.avg_duration_seconds/60:.1f} minutes",
                    "recommendation": f"Optimize {skill_name} for faster execution",
                })

        # Based on patterns
        for pattern in self.patterns:
            if pattern.pattern_type == "failure" and pattern.confidence > 0.6:
                recommendations.append({
                    "type": "failure_prevention",
                    "priority": "high" if pattern.confidence > 0.8 else "medium",
                    "pattern": pattern.description,
                    "recommendation": f"Add safeguards for: {pattern.description}",
                })

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        return sorted(recommendations, key=lambda r: priority_order.get(r["priority"], 1))

    # ========== Procedural Memory Integration ==========

    def export_to_procedural_memory(self) -> List[dict]:
        """Export successful patterns to procedural memory format."""
        procedural_entries = []

        # Export successful patterns as skills
        for pattern in self.patterns:
            if pattern.pattern_type == "success" and pattern.confidence > 0.7:
                procedural_entries.append({
                    "skill_name": f"learned_{pattern.pattern_type}_{pattern.pattern_id[:8]}",
                    "pattern_type": pattern.pattern_type,
                    "description": pattern.description,
                    "implementation": {
                        "pattern": pattern.description,
                        "steps": pattern.evidence,
                    },
                    "success_rate": pattern.confidence,
                })

        # Export optimized metrics
        for skill_name, metrics in self.skill_metrics.items():
            if metrics.success_rate > 0.9 and metrics.total_executions >= 5:
                procedural_entries.append({
                    "skill_name": skill_name,
                    "pattern_type": "optimized",
                    "description": f"Highly successful {skill_name} configuration",
                    "implementation": {
                        "avg_duration": metrics.avg_duration_seconds,
                        "expected_success_rate": metrics.success_rate,
                    },
                    "success_rate": metrics.success_rate,
                })

        return procedural_entries

    # ========== Dashboard ==========

    def get_dashboard(self) -> dict:
        """Get quality metrics dashboard."""
        total_executions = len(self.execution_records)
        successful = sum(1 for r in self.execution_records if r.success)
        failed = total_executions - successful

        # Recent executions (last 24 hours)
        cutoff = datetime.utcnow() - timedelta(days=1)
        recent = [
            r for r in self.execution_records
            if datetime.fromisoformat(r.started_at) > cutoff
        ]

        # Task type breakdown
        by_type = defaultdict(lambda: {"success": 0, "failed": 0})
        for record in recent:
            by_type[record.task_type]["success" if record.success else "failed"] += 1

        return {
            "total_executions": total_executions,
            "overall_success_rate": successful / total_executions if total_executions > 0 else 0,
            "recent_executions": len(recent),
            "recent_success_rate": sum(1 for r in recent if r.success) / len(recent) if recent else 0,
            "by_task_type": dict(by_type),
            "active_skills": len(self.skill_metrics),
            "patterns_learned": len(self.patterns),
            "recommendations_count": len(self.get_recommendations()),
            "last_updated": datetime.utcnow().isoformat(),
        }


if __name__ == "__main__":
    # Test self-improver
    improver = SelfImprover()

    # Record some sample executions
    for i in range(5):
        record = ExecutionRecord(
            task_id=f"task_{i}",
            task_type="research",
            agent_id="researcher",
            started_at=datetime.utcnow().isoformat(),
            completed_at=datetime.utcnow().isoformat(),
            duration_seconds=120 + i * 10,
            success=i < 4,  # 80% success rate
            steps_completed=["search", "fetch", "analyze"],
        )
        improver.record_execution(record)

    # Analyze patterns
    patterns = improver.analyze_patterns()
    print(f"Found {len(patterns)} patterns")

    # Get recommendations
    recs = improver.get_recommendations()
    print(f"Generated {len(recs)} recommendations")

    # Get dashboard
    dashboard = improver.get_dashboard()
    print(f"Dashboard: {json.dumps(dashboard, indent=2)}")

    # Export to procedural memory
    procedural = improver.export_to_procedural_memory()
    print(f"Exported {len(procedural)} procedural entries")
