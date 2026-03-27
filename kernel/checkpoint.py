"""
Checkpoint - State persistence for resume capability.
Saves and restores agent state including current task, context, and progress.
"""

import json
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Any
from dataclasses import dataclass, asdict, field
from enum import Enum


class CheckpointStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentState:
    """Complete state of an agent session."""
    checkpoint_id: str
    session_id: str
    status: str
    current_task_id: Optional[str] = None
    current_phase: str = "observe"  # observe, reason, act, checkpoint
    context: dict = field(default_factory=dict)
    memory_snapshot: dict = field(default_factory=dict)
    task_progress: dict = field(default_factory=dict)
    created_at: str = None
    updated_at: str = None
    last_checkpoint_at: Optional[str] = None
    version: int = 1

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AgentState":
        return cls(**data)


@dataclass
class TaskProgress:
    """Progress tracking for individual tasks."""
    task_id: str
    agent_id: str
    progress_percent: int = 0
    current_step: str = ""
    steps_completed: list = field(default_factory=list)
    steps_pending: list = field(default_factory=list)
    output_preview: Optional[str] = None
    started_at: str = None
    updated_at: str = None

    def __post_init__(self):
        if self.started_at is None:
            self.started_at = datetime.utcnow().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "TaskProgress":
        return cls(**data)


class CheckpointManager:
    """Manages agent state checkpoints for resume capability."""

    def __init__(self, base_path: str = "C:/Users/Shiva/Downloads/agent-os/memory/working"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.checkpoints_path = self.base_path / "checkpoints"
        self.checkpoints_path.mkdir(exist_ok=True)
        self.active_path = self.base_path / "active.json"

    def create_checkpoint(
        self,
        session_id: str,
        current_task_id: str = None,
        context: dict = None,
        memory_snapshot: dict = None,
        task_progress: dict = None
    ) -> AgentState:
        """Create a new checkpoint with current agent state."""
        checkpoint = AgentState(
            checkpoint_id=str(uuid.uuid4()),
            session_id=session_id,
            status=CheckpointStatus.ACTIVE.value,
            current_task_id=current_task_id,
            context=context or {},
            memory_snapshot=memory_snapshot or {},
            task_progress=task_progress or {}
        )

        self._save_checkpoint(checkpoint)
        self._save_active(checkpoint)

        return checkpoint

    def _save_checkpoint(self, checkpoint: AgentState) -> None:
        """Save checkpoint to file."""
        checkpoint_file = self.checkpoints_path / f"{checkpoint.checkpoint_id}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint.to_dict(), f, indent=2)

    def _save_active(self, checkpoint: AgentState) -> None:
        """Save as active checkpoint (most recent)."""
        checkpoint.last_checkpoint_at = datetime.utcnow().isoformat()
        checkpoint.updated_at = datetime.utcnow().isoformat()
        with open(self.active_path, 'w') as f:
            json.dump(checkpoint.to_dict(), f, indent=2)

    def get_active(self) -> Optional[AgentState]:
        """Get the current active checkpoint."""
        if not self.active_path.exists():
            return None
        with open(self.active_path, 'r') as f:
            return AgentState.from_dict(json.load(f))

    def get_checkpoint(self, checkpoint_id: str) -> Optional[AgentState]:
        """Get a specific checkpoint by ID."""
        checkpoint_file = self.checkpoints_path / f"{checkpoint_id}.json"
        if not checkpoint_file.exists():
            return None
        with open(checkpoint_file, 'r') as f:
            return AgentState.from_dict(json.load(f))

    def update_checkpoint(
        self,
        checkpoint_id: str = None,
        updates: dict = None
    ) -> Optional[AgentState]:
        """Update specific fields of a checkpoint."""
        if checkpoint_id is None:
            checkpoint = self.get_active()
            if not checkpoint:
                return None
            checkpoint_id = checkpoint.checkpoint_id
        else:
            checkpoint = self.get_checkpoint(checkpoint_id)
            if not checkpoint:
                return None

        if updates:
            for key, value in updates.items():
                if hasattr(checkpoint, key):
                    setattr(checkpoint, key, value)

        checkpoint.updated_at = datetime.utcnow().isoformat()
        self._save_checkpoint(checkpoint)
        self._save_active(checkpoint)

        return checkpoint

    def update_phase(self, phase: str) -> Optional[AgentState]:
        """Update the current phase of the active checkpoint."""
        return self.update_checkpoint(updates={"current_phase": phase})

    def suspend(self, checkpoint_id: str = None) -> bool:
        """Suspend the checkpoint (agent paused)."""
        checkpoint = self.get_checkpoint(checkpoint_id) if checkpoint_id else self.get_active()
        if not checkpoint:
            return False
        checkpoint.status = CheckpointStatus.SUSPENDED.value
        checkpoint.updated_at = datetime.utcnow().isoformat()
        self._save_checkpoint(checkpoint)
        self._save_active(checkpoint)
        return True

    def resume(self, checkpoint_id: str = None) -> Optional[AgentState]:
        """Resume a suspended checkpoint."""
        checkpoint = self.get_checkpoint(checkpoint_id) if checkpoint_id else self.get_active()
        if not checkpoint:
            return None
        checkpoint.status = CheckpointStatus.ACTIVE.value
        checkpoint.updated_at = datetime.utcnow().isoformat()
        self._save_checkpoint(checkpoint)
        self._save_active(checkpoint)
        return checkpoint

    def complete(self, checkpoint_id: str = None) -> bool:
        """Mark checkpoint as completed."""
        checkpoint = self.get_checkpoint(checkpoint_id) if checkpoint_id else self.get_active()
        if not checkpoint:
            return False
        checkpoint.status = CheckpointStatus.COMPLETED.value
        checkpoint.updated_at = datetime.utcnow().isoformat()
        self._save_checkpoint(checkpoint)
        # Remove active reference
        if self.active_path.exists():
            self.active_path.unlink()
        return True

    def save_task_progress(
        self,
        task_id: str,
        agent_id: str,
        progress_percent: int,
        current_step: str = "",
        steps_completed: list = None,
        output_preview: str = None
    ) -> None:
        """Save progress for a specific task."""
        progress = TaskProgress(
            task_id=task_id,
            agent_id=agent_id,
            progress_percent=progress_percent,
            current_step=current_step,
            steps_completed=steps_completed or [],
            output_preview=output_preview
        )

        progress_file = self.base_path / f"task_progress_{task_id}.json"
        with open(progress_file, 'w') as f:
            json.dump(progress.to_dict(), f, indent=2)

    def get_task_progress(self, task_id: str) -> Optional[TaskProgress]:
        """Get progress for a specific task."""
        progress_file = self.base_path / f"task_progress_{task_id}.json"
        if not progress_file.exists():
            return None
        with open(progress_file, 'r') as f:
            return TaskProgress.from_dict(json.load(f))

    def list_checkpoints(self, session_id: str = None) -> list:
        """List all checkpoints, optionally filtered by session."""
        checkpoints = []
        for checkpoint_file in self.checkpoints_path.glob("*.json"):
            with open(checkpoint_file, 'r') as f:
                cp = AgentState.from_dict(json.load(f))
                if session_id is None or cp.session_id == session_id:
                    checkpoints.append(cp)
        return sorted(checkpoints, key=lambda c: c.created_at, reverse=True)

    def delete_old_checkpoints(self, keep_last: int = 10) -> int:
        """Delete old checkpoints, keeping the most recent ones."""
        checkpoints = self.list_checkpoints()
        deleted = 0

        for checkpoint in checkpoints[keep_last:]:
            if checkpoint.status in [CheckpointStatus.COMPLETED.value, CheckpointStatus.FAILED.value]:
                checkpoint_file = self.checkpoints_path / f"{checkpoint.checkpoint_id}.json"
                if checkpoint_file.exists():
                    checkpoint_file.unlink()
                    deleted += 1

        return deleted


if __name__ == "__main__":
    # Test checkpoint functionality
    cm = CheckpointManager()

    # Create checkpoint
    cp = cm.create_checkpoint(
        session_id="test-session-001",
        current_task_id="task-123",
        context={"query": "AI trends", "depth": "comprehensive"},
        memory_snapshot={"recent": ["search1", "search2"]}
    )
    print(f"Created checkpoint: {cp.checkpoint_id}")

    # Update phase
    cm.update_phase("reason")
    cp = cm.get_active()
    print(f"Current phase: {cp.current_phase}")

    # Update progress
    cm.save_task_progress(
        task_id="task-123",
        agent_id="researcher-1",
        progress_percent=50,
        current_step="Extracting search results",
        steps_completed=["Query analysis", "Search execution"]
    )

    # Get progress
    progress = cm.get_task_progress("task-123")
    print(f"Task progress: {progress.progress_percent}% - {progress.current_step}")

    # Complete
    cm.complete()
    print(f"Checkpoint completed")
