"""
Skill Loader - On-demand loading of skills for the Agent OS.
Supports loading from filesystem and dynamically invoking skills.
"""

import json
import importlib.util
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum


class SkillCategory(Enum):
    RESEARCH = "research"
    PLANNING = "planning"
    EXECUTION = "execution"
    SYNTHESIS = "synthesis"
    UTILITY = "utility"
    INTEGRATION = "integration"


@dataclass
class Skill:
    """A skill that can be loaded and executed."""
    name: str
    category: str
    description: str
    version: str = "1.0.0"
    author: str = "Agent OS"
    dependencies: list = field(default_factory=list)
    parameters: dict = field(default_factory=dict)  # Expected parameters schema
    source_file: str = ""  # Path to skill implementation
    loaded_at: Optional[str] = None
    use_count: int = 0
    success_count: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Skill":
        return cls(**data)

    def success_rate(self) -> float:
        if self.use_count == 0:
            return 1.0
        return self.success_count / self.use_count


@dataclass
class SkillManifest:
    """Manifest of all available skills."""
    skills: Dict[str, Skill] = {}
    manifest_path: str = ""

    def to_dict(self) -> dict:
        return {
            "skills": {k: v.to_dict() for k, v in self.skills.items()},
            "generated_at": datetime.utcnow().isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SkillManifest":
        manifest = cls()
        for k, v in data.get("skills", {}).items():
            manifest.skills[k] = Skill.from_dict(v)
        return manifest


class SkillLoader:
    """
    On-demand skill loader for Agent OS.

    Features:
    - Discovers skills from filesystem
    - Loads skills on demand
    - Tracks skill usage and success rates
    - Manages skill dependencies
    - Caches loaded skills in memory
    """

    def __init__(
        self,
        skills_base_path: str = "C:/Users/Shiva/Downloads/agent-os/skills",
        registry_path: str = "C:/Users/Shiva/Downloads/agent-os/memory/procedural/skills.json"
    ):
        self.skills_base_path = Path(skills_base_path)
        self.registry_path = Path(registry_path)
        self.loaded_skills: Dict[str, Skill] = {}  # In-memory cache
        self.skill_functions: Dict[str, Callable] = {}  # Loaded skill functions

        # Ensure directories exist
        self.skills_base_path.mkdir(parents=True, exist_ok=True)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        # Load registry or create new
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> SkillManifest:
        """Load skill manifest from registry."""
        if self.registry_path.exists():
            with open(self.registry_path, 'r') as f:
                return SkillManifest.from_dict(json.load(f))
        return SkillManifest()

    def _save_manifest(self) -> None:
        """Save skill manifest to registry."""
        self.manifest.manifest_path = str(self.registry_path)
        with open(self.registry_path, 'w') as f:
            json.dump(self.manifest.to_dict(), f, indent=2)

    def discover_skills(self) -> List[Skill]:
        """Discover all skills in the skills directory."""
        discovered = []

        for skill_dir in self.skills_base_path.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_md = skill_dir / "SKILL.md"
            skill_json = skill_dir / "skill.json"

            if skill_md.exists():
                # Parse skill from markdown
                skill = self._parse_skill_md(skill_dir.name, skill_md.read_text())
                discovered.append(skill)
                self.manifest.skills[skill.name] = skill

        self._save_manifest()
        return discovered

    def _parse_skill_md(self, name: str, content: str) -> Skill:
        """Parse skill metadata from SKILL.md frontmatter."""
        lines = content.strip().split('\n')
        metadata = {}
        in_frontmatter = False
        frontmatter_lines = []

        for line in lines:
            if line.strip() == '---':
                in_frontmatter = not in_frontmatter
                continue
            if in_frontmatter:
                frontmatter_lines.append(line)
            elif line.startswith('#'):
                metadata['description'] = line.lstrip('#').strip()
                break

        # Parse frontmatter
        for line in frontmatter_lines:
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()

        return Skill(
            name=name,
            category=metadata.get('category', 'utility'),
            description=metadata.get('description', ''),
            version=metadata.get('version', '1.0.0'),
            source_file=str(self.skills_base_path / name / "SKILL.md")
        )

    def register_skill(self, skill: Skill) -> None:
        """Manually register a skill."""
        self.manifest.skills[skill.name] = skill
        self._save_manifest()

    def load_skill(self, skill_name: str) -> Optional[Skill]:
        """Load a skill into memory."""
        if skill_name in self.loaded_skills:
            return self.loaded_skills[skill_name]

        skill = self.manifest.skills.get(skill_name)
        if not skill:
            return None

        # Mark as loaded
        skill.loaded_at = datetime.utcnow().isoformat()
        self.loaded_skills[skill_name] = skill

        return skill

    def get_skill(self, skill_name: str) -> Optional[Skill]:
        """Get a skill (loads if not already loaded)."""
        if skill_name not in self.loaded_skills:
            return self.load_skill(skill_name)
        return self.loaded_skills[skill_name]

    def unload_skill(self, skill_name: str) -> bool:
        """Unload a skill from memory."""
        if skill_name in self.loaded_skills:
            del self.loaded_skills[skill_name]
            if skill_name in self.skill_functions:
                del self.skill_functions[skill_name]
            return True
        return False

    def get_available_skills(self) -> List[Skill]:
        """Get list of all available skills."""
        return list(self.manifest.skills.values())

    def get_skills_by_category(self, category: str) -> List[Skill]:
        """Get all skills in a specific category."""
        return [
            s for s in self.manifest.skills.values()
            if s.category == category
        ]

    def record_skill_use(self, skill_name: str, success: bool) -> bool:
        """Record skill usage and success/failure."""
        skill = self.get_skill(skill_name)
        if not skill:
            return False

        skill.use_count += 1
        if success:
            skill.success_count += 1

        self._save_manifest()
        return True

    def get_skill_stats(self) -> dict:
        """Get statistics about loaded skills."""
        total = len(self.manifest.skills)
        loaded = len(self.loaded_skills)
        total_uses = sum(s.use_count for s in self.manifest.skills.values())

        return {
            "total_skills": total,
            "loaded_skills": loaded,
            "total_uses": total_uses,
            "categories": self._count_by_category(),
        }

    def _count_by_category(self) -> dict:
        """Count skills by category."""
        counts = {}
        for skill in self.manifest.skills.values():
            counts[skill.category] = counts.get(skill.category, 0) + 1
        return counts

    def invoke_skill(self, skill_name: str, parameters: dict = None) -> Any:
        """
        Invoke a skill with parameters.
        This is a placeholder - actual skill invocation depends on skill type.
        """
        skill = self.load_skill(skill_name)
        if not skill:
            raise ValueError(f"Skill not found: {skill_name}")

        skill.use_count += 1
        self._save_manifest()

        # For now, return skill info - actual execution would load and run skill code
        return {
            "skill": skill.name,
            "status": "invoked",
            "parameters": parameters or {},
        }

    def create_skill(
        self,
        name: str,
        category: str,
        description: str,
        implementation: str,  # Python code as string
        parameters: dict = None
    ) -> Skill:
        """Create and register a new skill."""
        # Create skill directory
        skill_dir = self.skills_base_path / name
        skill_dir.mkdir(exist_ok=True)

        # Write SKILL.md
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(f"""---
name: {name}
category: {category}
description: {description}
version: 1.0.0
---

# {name}

{description}

## Usage

```
/skill {name}
```

## Parameters

{json.dumps(parameters or {}, indent=2)}
""")

        # Write implementation if provided
        if implementation:
            skill_py = skill_dir / "skill.py"
            skill_py.write_text(implementation)

        # Create skill object
        skill = Skill(
            name=name,
            category=category,
            description=description,
            source_file=str(skill_dir / "SKILL.md"),
            parameters=parameters or {}
        )

        self.register_skill(skill)
        return skill


if __name__ == "__main__":
    # Test skill loader
    loader = SkillLoader()

    # Discover skills
    discovered = loader.discover_skills()
    print(f"Discovered {len(discovered)} skills")

    # Get stats
    print(f"Skill stats: {loader.get_skill_stats()}")

    # Create a test skill
    test_skill = loader.create_skill(
        name="web_research",
        category="research",
        description="Perform deep web research on a topic",
        implementation="""def research(query, depth='comprehensive'):
    return {'query': query, 'depth': depth, 'results': []}
""",
        parameters={
            "query": {"type": "string", "required": True},
            "depth": {"type": "string", "default": "standard"},
        }
    )
    print(f"Created skill: {test_skill.name}")

    # Load and invoke
    loaded = loader.load_skill("web_research")
    if loaded:
        result = loader.invoke_skill("web_research", {"query": "AI trends"})
        print(f"Invoked: {result}")
