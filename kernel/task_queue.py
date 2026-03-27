"""
Task Queue - File-based JSON queue with atomic operations, retry logic, and dead-letter handling.
"""

import json
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, asdict
from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class TaskType(Enum):
    RESEARCH = "research"
    PLAN = "plan"
    EXECUTE = "execute"
    SYNTHESIZE = "synthesize"


@dataclass
class Task:
    id: str
    type: str
    status: str
    priority: int  # 1-10, 10 being highest
    attempt_count: int = 0
    max_attempts: int = 3
    input: dict = None
    output: Optional[dict] = None
    error: Optional[str] = None
    dependencies: list = None
    blocked_by: list = None
    created_at: str = None
    updated_at: str = None
    completed_at: Optional[str] = None

    def __post_init__(self):
        if self.input is None:
            self.input = {}
        if self.dependencies is None:
            self.dependencies = []
        if self.blocked_by is None:
            self.blocked_by = []
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(**data)


class TaskQueue:
    """File-based task queue with atomic operations."""

    def __init__(self, base_path: str = "C:/Users/Shiva/Downloads/agent-os/queue"):
        self.base_path = Path(base_path)
        self.pending_path = self.base_path / "pending"
        self.in_progress_path = self.base_path / "in_progress"
        self.completed_path = self.base_path / "completed"
        self.dead_letter_path = self.base_path / "dead_letter"

        # Ensure directories exist
        for path in [self.pending_path, self.in_progress_path, self.completed_path, self.dead_letter_path]:
            path.mkdir(parents=True, exist_ok=True)

    def _task_file_path(self, task_id: str, status: TaskStatus) -> Path:
        """Get the file path for a task based on its status."""
        status_map = {
            TaskStatus.PENDING: self.pending_path,
            TaskStatus.IN_PROGRESS: self.in_progress_path,
            TaskStatus.COMPLETED: self.completed_path,
            TaskStatus.FAILED: self.dead_letter_path,
            TaskStatus.DEAD_LETTER: self.dead_letter_path,
        }
        return status_map[status] / f"{task_id}.json"

    def _read_task(self, task_id: str) -> Optional[Task]:
        """Read a task from any queue."""
        for path in [self.pending_path, self.in_progress_path, self.completed_path, self.dead_letter_path]:
            task_file = path / f"{task_id}.json"
            if task_file.exists():
                with open(task_file, 'r') as f:
                    return Task.from_dict(json.load(f))
        return None

    def _write_task_atomic(self, task: Task, status: TaskStatus) -> None:
        """Write task atomically to the correct queue."""
        task.updated_at = datetime.utcnow().isoformat()
        task.status = status.value

        new_path = self._task_file_path(task.id, status)
        temp_path = new_path.with_suffix('.tmp')

        with open(temp_path, 'w') as f:
            json.dump(task.to_dict(), f, indent=2)

        temp_path.replace(new_path)

    def enqueue(
        self,
        task_type: str,
        input_data: dict,
        priority: int = 5,
        dependencies: list = None,
        blocked_by: list = None,
        max_attempts: int = 3
    ) -> Task:
        """Create and enqueue a new task."""
        task = Task(
            id=str(uuid.uuid4()),
            type=task_type,
            status=TaskStatus.PENDING.value,
            priority=priority,
            input=input_data,
            dependencies=dependencies or [],
            blocked_by=blocked_by or [],
            max_attempts=max_attempts
        )

        self._write_task_atomic(task, TaskStatus.PENDING)
        return task

    def dequeue(self) -> Optional[Task]:
        """Get the highest priority task that has no blocked_by dependencies."""
        pending_tasks = []

        for task_file in self.pending_path.glob("*.json"):
            with open(task_file, 'r') as f:
                task = Task.from_dict(json.load(f))
                pending_tasks.append(task)

        # Filter out blocked tasks
        available_tasks = []
        for task in pending_tasks:
            if task.blocked_by:
                # Check if all blocking tasks are completed
                all_blocked_completed = all(
                    self._get_task_status(blocked_id) == TaskStatus.COMPLETED.value
                    for blocked_id in task.blocked_by
                )
                if not all_blocked_completed:
                    continue
            available_tasks.append(task)

        if not available_tasks:
            return None

        # Sort by priority (descending) then by created_at (ascending)
        available_tasks.sort(key=lambda t: (-t.priority, t.created_at))

        task = available_tasks[0]
        task.status = TaskStatus.IN_PROGRESS.value
        task.attempt_count += 1
        task.updated_at = datetime.utcnow().isoformat()

        # Move to in_progress
        old_path = self.pending_path / f"{task.id}.json"
        new_path = self.in_progress_path / f"{task.id}.json"

        # Write new file first
        with open(new_path, 'w') as f:
            json.dump(task.to_dict(), f, indent=2)

        # Remove old file
        old_path.unlink()

        return task

    def _get_task_status(self, task_id: str) -> Optional[str]:
        """Get the current status of a task."""
        for path, status in [
            (self.pending_path, TaskStatus.PENDING),
            (self.in_progress_path, TaskStatus.IN_PROGRESS),
            (self.completed_path, TaskStatus.COMPLETED),
            (self.dead_letter_path, TaskStatus.DEAD_LETTER),
        ]:
            if (path / f"{task_id}.json").exists():
                return status.value
        return None

    def complete(self, task_id: str, output: dict) -> bool:
        """Mark a task as completed with output."""
        task = self._read_task(task_id)
        if not task:
            return False

        task.status = TaskStatus.COMPLETED.value
        task.output = output
        task.completed_at = datetime.utcnow().isoformat()
        task.updated_at = datetime.utcnow().isoformat()

        # Move to completed
        old_path = self.in_progress_path / f"{task_id}.json"
        new_path = self.completed_path / f"{task_id}.json"

        with open(new_path, 'w') as f:
            json.dump(task.to_dict(), f, indent=2)

        old_path.unlink()
        return True

    def fail(self, task_id: str, error: str) -> bool:
        """Mark a task as failed. If max attempts reached, move to dead letter."""
        task = self._read_task(task_id)
        if not task:
            return False

        task.error = error
        task.attempt_count += 1  # Increment on each failure
        task.updated_at = datetime.utcnow().isoformat()

        if task.attempt_count >= task.max_attempts:
            # Move to dead letter
            task.status = TaskStatus.DEAD_LETTER.value
            new_path = self.dead_letter_path / f"{task_id}.json"
        else:
            # Move back to pending for retry
            task.status = TaskStatus.PENDING.value
            new_path = self.pending_path / f"{task_id}.json"

        old_path = self.in_progress_path / f"{task_id}.json"

        with open(new_path, 'w') as f:
            json.dump(task.to_dict(), f, indent=2)

        if old_path.exists():
            old_path.unlink()

        return True

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID from any queue."""
        return self._read_task(task_id)

    def get_queue_stats(self) -> dict:
        """Get statistics about all queues."""
        def count_tasks(path: Path) -> int:
            return len(list(path.glob("*.json")))

        return {
            "pending": count_tasks(self.pending_path),
            "in_progress": count_tasks(self.in_progress_path),
            "completed": count_tasks(self.completed_path),
            "dead_letter": count_tasks(self.dead_letter_path),
        }

    def get_pending_tasks(self) -> list:
        """Get all pending tasks sorted by priority."""
        tasks = []
        for task_file in self.pending_path.glob("*.json"):
            with open(task_file, 'r') as f:
                tasks.append(Task.from_dict(json.load(f)))
        return sorted(tasks, key=lambda t: (-t.priority, t.created_at))

    def get_in_progress_tasks(self) -> list:
        """Get all in-progress tasks."""
        tasks = []
        for task_file in self.in_progress_path.glob("*.json"):
            with open(task_file, 'r') as f:
                tasks.append(Task.from_dict(json.load(f)))
        return tasks

    def get_dead_letter_tasks(self) -> list:
        """Get all dead letter tasks."""
        tasks = []
        for task_file in self.dead_letter_path.glob("*.json"):
            with open(task_file, 'r') as f:
                tasks.append(Task.from_dict(json.load(f)))
        return tasks

    def requeue_dead_letter(self, task_id: str, max_attempts: int = 5) -> bool:
        """Requeue a dead letter task with a new max_attempts."""
        task = self._read_task(task_id)
        if not task or task.status != TaskStatus.DEAD_LETTER.value:
            return False

        # Reset the task
        task.status = TaskStatus.PENDING.value
        task.attempt_count = 0
        task.max_attempts = max_attempts
        task.error = None
        task.updated_at = datetime.utcnow().isoformat()

        # Move to pending
        old_path = self.dead_letter_path / f"{task_id}.json"
        new_path = self.pending_path / f"{task_id}.json"

        with open(new_path, 'w') as f:
            json.dump(task.to_dict(), f, indent=2)

        old_path.unlink()
        return True

    def clear_completed(self, older_than_days: int = 7) -> int:
        """Clear completed tasks older than specified days. Returns count of deleted tasks."""
        import time
        cutoff = datetime.utcnow().timestamp() - (older_than_days * 24 * 60 * 60)
        deleted = 0

        for task_file in self.completed_path.glob("*.json"):
            mtime = task_file.stat().st_mtime
            if mtime < cutoff:
                task_file.unlink()
                deleted += 1

        return deleted


if __name__ == "__main__":
    # Test the task queue
    queue = TaskQueue()

    # Test enqueue
    task = queue.enqueue(
        task_type=TaskType.RESEARCH.value,
        input_data={"query": "AI trends 2026"},
        priority=8
    )
    print(f"Enqueued task: {task.id}")

    # Test dequeue
    dequeued = queue.dequeue()
    print(f"Dequeued task: {dequeued.id if dequeued else None}")

    # Test complete
    if dequeued:
        queue.complete(dequeued.id, {"findings": ["AI is growing", "ML adoption increasing"]})
        print(f"Completed task: {dequeued.id}")

    # Test stats
    print(f"Queue stats: {queue.get_queue_stats()}")
