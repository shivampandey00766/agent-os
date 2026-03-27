"""
Memory System - 4-layer memory manager for Agent OS.

Layers:
- Working: Current session context
- Episodic: Past interactions (30 days)
- Semantic: Knowledge base, research results (permanent)
- Procedural: Learned skills, best practices (permanent)
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field
from enum import Enum


class MemoryLayer(Enum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


@dataclass
class MemoryEntry:
    """A single memory entry."""
    id: str
    layer: str
    content: dict
    tags: list = field(default_factory=list)
    created_at: str = None
    accessed_at: str = None
    access_count: int = 0
    importance: int = 5  # 1-10

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.accessed_at is None:
            self.accessed_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        return cls(**data)

    def touch(self):
        """Update access time and count."""
        self.accessed_at = datetime.utcnow().isoformat()
        self.access_count += 1


@dataclass
class Episode:
    """An episodic memory containing a complete interaction."""
    id: str
    session_id: str
    layer: str = "episodic"
    events: list = field(default_factory=list)  # List of event dicts
    summary: str = ""
    tags: list = field(default_factory=list)
    outcome: str = ""  # success, failure, partial
    duration_seconds: int = 0
    created_at: str = None
    ended_at: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Episode":
        return cls(**data)

    def add_event(self, event_type: str, data: dict):
        """Add an event to the episode."""
        self.events.append({
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        })

    def end(self, outcome: str):
        """End the episode with an outcome."""
        self.outcome = outcome
        self.ended_at = datetime.utcnow().isoformat()
        if self.created_at:
            created = datetime.fromisoformat(self.created_at)
            self.duration_seconds = int((datetime.utcnow() - created).total_seconds())


class MemoryManager:
    """
    4-layer memory system manager.

    Layer Retention:
    - Working: Current session only
    - Episodic: 30 days
    - Semantic: Permanent
    - Procedural: Permanent
    """

    def __init__(self, base_path: str = "C:/Users/Shiva/Downloads/agent-os/memory"):
        self.base_path = Path(base_path)

        # Create layer directories
        self.working_path = self.base_path / "working"
        self.episodic_path = self.base_path / "episodic"
        self.semantic_path = self.base_path / "semantic"
        self.procedural_path = self.base_path / "procedural"

        for path in [self.working_path, self.episodic_path, self.semantic_path, self.procedural_path]:
            path.mkdir(parents=True, exist_ok=True)

        self.episode_retention_days = 30

    # ========== WORKING MEMORY ==========

    def set_working(self, key: str, value: Any) -> None:
        """Set a working memory entry."""
        entry = MemoryEntry(
            id=key,
            layer=MemoryLayer.WORKING.value,
            content={"value": value},
        )
        self._write_entry(self.working_path, key, entry)

    def get_working(self, key: str) -> Optional[Any]:
        """Get a working memory entry."""
        entry = self._read_entry(self.working_path, key)
        if entry:
            entry.touch()
            self._write_entry(self.working_path, key, entry)
            return entry.content.get("value")
        return None

    def get_working_context(self) -> dict:
        """Get all working memory as context dict."""
        context = {}
        for file in self.working_path.glob("*.json"):
            with open(file, 'r') as f:
                entry = MemoryEntry.from_dict(json.load(f))
                context[entry.id] = entry.content.get("value")
        return context

    def clear_working(self) -> None:
        """Clear all working memory."""
        for file in self.working_path.glob("*.json"):
            file.unlink()

    # ========== EPISODIC MEMORY ==========

    def create_episode(self, session_id: str, summary: str = "", tags: list = None) -> Episode:
        """Create a new episodic memory episode."""
        episode = Episode(
            id=str(uuid.uuid4()),
            session_id=session_id,
            summary=summary,
            tags=tags or [],
        )
        self._write_episode(episode)
        return episode

    def add_to_episode(self, episode_id: str, event_type: str, data: dict) -> bool:
        """Add an event to an existing episode."""
        episode = self._read_episode(episode_id)
        if not episode:
            return False
        episode.add_event(event_type, data)
        self._write_episode(episode)
        return True

    def end_episode(self, episode_id: str, outcome: str) -> bool:
        """End an episode with outcome."""
        episode = self._read_episode(episode_id)
        if not episode:
            return False
        episode.end(outcome)
        self._write_episode(episode)
        return True

    def get_episode(self, episode_id: str) -> Optional[Episode]:
        """Get a specific episode."""
        return self._read_episode(episode_id)

    def get_recent_episodes(self, limit: int = 10) -> List[Episode]:
        """Get most recent episodes."""
        episodes = []
        for file in self.episodic_path.glob("ep_*.json"):
            with open(file, 'r') as f:
                episodes.append(Episode.from_dict(json.load(f)))
        return sorted(episodes, key=lambda e: e.created_at, reverse=True)[:limit]

    def query_episodes(self, query: str, tags: list = None, limit: int = 10) -> List[Episode]:
        """Search episodes by content or tags."""
        results = []
        query_lower = query.lower()

        for file in self.episodic_path.glob("ep_*.json"):
            with open(file, 'r') as f:
                episode = Episode.from_dict(json.load(f))

                # Check if query matches summary or events
                matches = query_lower in episode.summary.lower()
                if not matches:
                    for event in episode.events:
                        if query_lower in str(event.get("data", "")).lower():
                            matches = True
                            break

                # Check tags
                if tags:
                    matches = matches or any(tag in episode.tags for tag in tags)

                if matches:
                    results.append(episode)

        sorted_results = sorted(results, key=lambda e: e.created_at, reverse=True)
        return sorted_results[:limit]

    def _read_episode(self, episode_id: str) -> Optional[Episode]:
        """Read an episode from file."""
        episode_file = self.episodic_path / f"ep_{episode_id}.json"
        if not episode_file.exists():
            return None
        with open(episode_file, 'r') as f:
            return Episode.from_dict(json.load(f))

    def _write_episode(self, episode: Episode) -> None:
        """Write episode to file."""
        episode_file = self.episodic_path / f"ep_{episode.id}.json"
        with open(episode_file, 'w') as f:
            json.dump(episode.to_dict(), f, indent=2)

    def cleanup_old_episodes(self) -> int:
        """Delete episodes older than retention period. Returns count deleted."""
        cutoff = datetime.utcnow() - timedelta(days=self.episode_retention_days)
        deleted = 0

        for file in self.episodic_path.glob("ep_*.json"):
            with open(file, 'r') as f:
                episode = Episode.from_dict(json.load(f))

            created = datetime.fromisoformat(episode.created_at)
            if created < cutoff:
                file.unlink()
                deleted += 1

        return deleted

    # ========== SEMANTIC MEMORY ==========

    def add_semantic(self, key: str, content: dict, tags: list = None, importance: int = 5) -> MemoryEntry:
        """Add a semantic memory entry (knowledge base)."""
        entry = MemoryEntry(
            id=key,
            layer=MemoryLayer.SEMANTIC.value,
            content=content,
            tags=tags or [],
            importance=importance,
        )
        self._write_entry(self.semantic_path, key, entry)
        return entry

    def get_semantic(self, key: str) -> Optional[MemoryEntry]:
        """Get a semantic memory entry."""
        entry = self._read_entry(self.semantic_path, key)
        if entry:
            entry.touch()
            self._write_entry(self.semantic_path, key, entry)
        return entry

    def query_semantic(self, query: str, tags: list = None, limit: int = 10) -> List[MemoryEntry]:
        """Query semantic memory for relevant entries."""
        results = []
        query_lower = query.lower()

        for file in self.semantic_path.glob("*.json"):
            with open(file, 'r') as f:
                entry = MemoryEntry.from_dict(json.load(f))

            # Check if query matches content or tags
            content_str = str(entry.content).lower()
            matches = query_lower in content_str
            if not matches and entry.tags:
                matches = any(query_lower in tag.lower() for tag in entry.tags)

            if tags and entry.tags:
                matches = matches and any(tag in entry.tags for tag in tags)

            if matches:
                results.append(entry)

        # Sort by importance and access count
        results.sort(key=lambda e: (-e.importance, -e.access_count))
        return results[:limit]

    def get_all_semantic_tags(self) -> List[str]:
        """Get all unique tags in semantic memory."""
        tags = set()
        for file in self.semantic_path.glob("*.json"):
            with open(file, 'r') as f:
                entry = MemoryEntry.from_dict(json.load(f))
                tags.update(entry.tags)
        return sorted(tags)

    # ========== PROCEDURAL MEMORY ==========

    def add_procedural(self, skill_name: str, implementation: dict, pattern_type: str, success_rate: float = 1.0) -> MemoryEntry:
        """Add a procedural memory entry (learned skill/pattern)."""
        entry = MemoryEntry(
            id=skill_name,
            layer=MemoryLayer.PROCEDURAL.value,
            content={
                "implementation": implementation,
                "pattern_type": pattern_type,
                "success_rate": success_rate,
                "use_count": 0,
            },
            tags=[pattern_type, "skill"],
            importance=7,
        )
        self._write_entry(self.procedural_path, skill_name, entry)
        return entry

    def get_procedural(self, skill_name: str) -> Optional[MemoryEntry]:
        """Get a procedural memory entry."""
        entry = self._read_entry(self.procedural_path, skill_name)
        if entry:
            entry.content["use_count"] = entry.content.get("use_count", 0) + 1
            entry.touch()
            self._write_entry(self.procedural_path, skill_name, entry)
        return entry

    def get_procedurals_by_pattern(self, pattern_type: str) -> List[MemoryEntry]:
        """Get all procedural entries of a specific pattern type."""
        results = []
        for file in self.procedural_path.glob("*.json"):
            with open(file, 'r') as f:
                entry = MemoryEntry.from_dict(json.load(f))
                if pattern_type in entry.tags:
                    results.append(entry)
        return sorted(results, key=lambda e: -e.content.get("success_rate", 0))

    def update_skill_success(self, skill_name: str, success: bool) -> bool:
        """Update the success rate of a skill based on execution result."""
        entry = self._read_entry(self.procedural_path, skill_name)
        if not entry:
            return False

        current_rate = entry.content.get("success_rate", 1.0)
        # Simple moving average
        new_rate = (current_rate * 0.8) + (1.0 if success else 0.0) * 0.2
        entry.content["success_rate"] = new_rate
        self._write_entry(self.procedural_path, skill_name, entry)
        return True

    # ========== UTILITY METHODS ==========

    def _write_entry(self, path: Path, key: str, entry: MemoryEntry) -> None:
        """Write a memory entry to file."""
        entry_file = path / f"{key}.json"
        with open(entry_file, 'w') as f:
            json.dump(entry.to_dict(), f, indent=2)

    def _read_entry(self, path: Path, key: str) -> Optional[MemoryEntry]:
        """Read a memory entry from file."""
        entry_file = path / f"{key}.json"
        if not entry_file.exists():
            return None
        with open(entry_file, 'r') as f:
            return MemoryEntry.from_dict(json.load(f))

    def query_similar(self, query: str, limit: int = 5) -> dict:
        """Query across all memory layers for similar content."""
        return {
            "semantic": self.query_semantic(query, limit=limit),
            "episodes": self.query_episodes(query, limit=limit),
            "procedural": self.get_procedurals_by_pattern(query),
        }

    def get_stats(self) -> dict:
        """Get memory system statistics."""
        return {
            "working_entries": len(list(self.working_path.glob("*.json"))),
            "episodic_entries": len(list(self.episodic_path.glob("*.json"))),
            "semantic_entries": len(list(self.semantic_path.glob("*.json"))),
            "procedural_entries": len(list(self.procedural_path.glob("*.json"))),
        }


if __name__ == "__main__":
    # Test memory system
    mm = MemoryManager()

    # Working memory
    mm.set_working("current_task", {"query": "AI trends 2026", "status": "in_progress"})
    print(f"Working: {mm.get_working('current_task')}")

    # Semantic memory
    mm.add_semantic(
        "ai_trends_2026",
        {"summary": "Key AI trends in 2026", "findings": ["LLM improvements", "AI agents"]},
        tags=["ai", "trends", "2026"],
        importance=8
    )
    results = mm.query_semantic("AI trends")
    print(f"Semantic results: {len(results)}")

    # Procedural memory
    mm.add_procedural("web_research", {"steps": ["search", "fetch", "extract"]}, "research")
    skill = mm.get_procedural("web_research")
    print(f"Skill success rate: {skill.content.get('success_rate') if skill else 'N/A'}")

    # Episode
    ep = mm.create_episode("session-001", "Research AI trends", tags=["research"])
    mm.add_to_episode(ep.id, "task_start", {"task": "research"})
    mm.add_to_episode(ep.id, "task_complete", {"results": "found 10 sources"})
    mm.end_episode(ep.id, "success")
    print(f"Episode duration: {mm.get_episode(ep.id).duration_seconds}s")

    # Stats
    print(f"Memory stats: {mm.get_stats()}")
