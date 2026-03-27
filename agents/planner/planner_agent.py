"""
Planner Agent - Task decomposition and planning implementation.
Breaks down complex goals into ordered subtasks with dependencies.
"""

import uuid
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class Subtask:
    """A decomposed subtask."""
    id: int
    description: str
    agent: str  # researcher, planner, executor, synthesizer
    priority: float
    blocked_by: List[int]
    estimated_duration: str
    status: str = "pending"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Subtask":
        return cls(**data)


@dataclass
class Plan:
    """A complete plan with decomposed subtasks."""
    plan_id: str
    goal: str
    goal_analysis: Dict
    constraints: Dict
    subtasks: List[Subtask]
    dependency_graph: Dict
    estimated_duration: str
    risks: List[Dict]
    summary: str

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "subtasks": [s.to_dict() if isinstance(s, Subtask) else s for s in self.subtasks]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Plan":
        subtasks = [Subtask.from_dict(t) if isinstance(t, dict) else t for t in data.get("subtasks", [])]
        return cls(subtasks=subtasks, **data)


class PlannerAgent:
    """
    Task decomposition and planning agent.

    Planning Protocol:
    1. Goal Analysis → End State Definition
    2. Constraint Identification
    3. Subtask Decomposition
    4. Dependency Mapping
    5. Priority Assignment
    6. Plan Generation
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.max_depth = 10
        self.max_subtasks = 50

    async def execute(self, task_input: dict, context: dict = None) -> dict:
        """
        Decompose a task into ordered subtasks.

        Args:
            task_input: {
                "goal": "End goal description",
                "constraints": {"time": "2 weeks", "budget": "limited"},
                "research_output": {...},  # Optional context from researcher
            }
            context: Additional context

        Returns:
            {
                "plan_id": "uuid",
                "goal": "...",
                "subtasks": [...],
                "dependency_graph": {...},
                "estimated_duration": "...",
                "risks": [...],
            }
        """
        goal = task_input.get("goal")
        constraints = task_input.get("constraints", {})
        research_output = task_input.get("research_output", {})

        # Step 1: Analyze goal
        goal_analysis = self._analyze_goal(goal, research_output)

        # Step 2: Identify constraints
        identified_constraints = self._identify_constraints(goal, constraints)

        # Step 3: Decompose into subtasks
        subtasks = self._decompose(
            goal_analysis,
            identified_constraints,
            context.get("available_agents", ["researcher", "planner", "executor", "synthesizer"]) if context else ["researcher", "planner", "executor", "synthesizer"]
        )

        # Step 4: Build dependency graph
        dependency_graph = self._build_dependency_graph(subtasks)

        # Step 5: Assign priorities
        prioritized = self._assign_priorities(subtasks, dependency_graph)

        # Step 6: Identify risks
        risks = self._identify_risks(prioritized, identified_constraints)

        plan = Plan(
            plan_id=str(uuid.uuid4()),
            goal=goal,
            goal_analysis=goal_analysis,
            constraints=identified_constraints,
            subtasks=prioritized,
            dependency_graph=dependency_graph,
            estimated_duration=self._estimate_duration(prioritized),
            risks=risks,
            summary=self._generate_plan_summary(prioritized)
        )

        return plan.to_dict()

    def _analyze_goal(self, goal: str, research: dict = None) -> dict:
        """Analyze the goal to understand requirements."""
        keywords = goal.lower().split()

        # Identify goal type
        if any(k in keywords for k in ["create", "build", "implement", "make", "develop"]):
            goal_type = "implementation"
        elif any(k in keywords for k in ["research", "analyze", "investigate", "study", "examine"]):
            goal_type = "research"
        elif any(k in keywords for k in ["compare", "evaluate", "assess", "review"]):
            goal_type = "evaluation"
        elif any(k in keywords for k in ["improve", "optimize", "enhance", "upgrade"]):
            goal_type = "improvement"
        elif any(k in keywords for k in ["design", "plan", "architect"]):
            goal_type = "design"
        else:
            goal_type = "general"

        # Identify key deliverables
        deliverables = self._extract_deliverables(goal)

        # Identify audience
        audience = self._extract_audience(goal)

        # Estimate complexity
        complexity = self._estimate_complexity(goal, research)

        return {
            "type": goal_type,
            "deliverables": deliverables,
            "audience": audience,
            "complexity": complexity,
        }

    def _extract_deliverables(self, goal: str) -> list:
        """Extract expected deliverables from goal."""
        deliverables = []
        goal_lower = goal.lower()

        if "report" in goal_lower:
            deliverables.append("report")
        if "analysis" in goal_lower:
            deliverables.append("analysis")
        if any(k in goal_lower for k in ["code", "implement", "build", "create"]):
            deliverables.append("code")
        if "recommendation" in goal_lower:
            deliverables.append("recommendations")
        if "comparison" in goal_lower:
            deliverables.append("comparison_matrix")
        if "design" in goal_lower:
            deliverables.append("design")
        if "plan" in goal_lower:
            deliverables.append("plan")
        if "prototype" in goal_lower:
            deliverables.append("prototype")

        return deliverables or ["outcome"]

    def _extract_audience(self, goal: str) -> str:
        """Extract target audience from goal."""
        goal_lower = goal.lower()

        if any(k in goal_lower for k in ["executive", "c-level", "ceo", "cfo", "cto"]):
            return "executives"
        elif any(k in goal_lower for k in ["technical", "engineer", "developer", "architect"]):
            return "technical"
        elif any(k in goal_lower for k in ["customer", "user", "client"]):
            return "end_users"
        elif any(k in goal_lower for k in ["marketing", "sales"]):
            return "business"
        else:
            return "general"

    def _estimate_complexity(self, goal: str, research: dict = None) -> str:
        """Estimate task complexity."""
        words = len(goal.split())

        # Check for complexity indicators
        has_comparison = any(k in goal.lower() for k in ["compare", "vs", "versus"])
        has_multiple_parts = " and " in goal.lower() or "," in goal
        has_research = research is not None

        if words > 30 or (has_comparison and has_multiple_parts):
            return "high"
        elif words > 15 or has_research:
            return "medium"
        else:
            return "low"

    def _identify_constraints(self, goal: str, provided: dict) -> dict:
        """Identify constraints on the task."""
        constraints = {**provided}
        goal_lower = goal.lower()

        # Time constraints
        time_keywords = {
            "urgent": {"time_urgency": "high"},
            "asap": {"time_urgency": "high"},
            "quick": {"time_urgency": "high"},
            "brief": {"time_urgency": "medium"},
            "thorough": {"quality": "high"},
            "comprehensive": {"quality": "high"},
            "detailed": {"quality": "high"},
            "simple": {"complexity": "low"},
        }

        for keyword, constraint in time_keywords.items():
            if keyword in goal_lower:
                constraints.update(constraint)

        return constraints

    def _decompose(self, goal_analysis: dict, constraints: dict, agents: list) -> List[Subtask]:
        """Decompose goal into subtasks."""
        subtasks = []
        goal_type = goal_analysis["type"]

        # Task templates by type
        templates = {
            "implementation": [
                {"description": "Review requirements and design", "agent": "planner", "priority": 10},
                {"description": "Set up development environment", "agent": "executor", "priority": 9},
                {"description": "Implement core functionality", "agent": "executor", "priority": 8},
                {"description": "Add tests and validation", "agent": "executor", "priority": 7},
                {"description": "Final review and documentation", "agent": "synthesizer", "priority": 6},
            ],
            "research": [
                {"description": "Define research questions", "agent": "planner", "priority": 10},
                {"description": "Gather data from sources", "agent": "researcher", "priority": 9},
                {"description": "Analyze and synthesize findings", "agent": "researcher", "priority": 8},
                {"description": "Generate report", "agent": "synthesizer", "priority": 7},
            ],
            "evaluation": [
                {"description": "Define evaluation criteria", "agent": "planner", "priority": 10},
                {"description": "Gather comparison data", "agent": "researcher", "priority": 9},
                {"description": "Perform evaluation", "agent": "executor", "priority": 8},
                {"description": "Generate comparison report", "agent": "synthesizer", "priority": 7},
            ],
            "improvement": [
                {"description": "Analyze current state", "agent": "researcher", "priority": 10},
                {"description": "Identify improvement areas", "agent": "planner", "priority": 9},
                {"description": "Implement improvements", "agent": "executor", "priority": 8},
                {"description": "Validate improvements", "agent": "executor", "priority": 7},
            ],
            "design": [
                {"description": "Understand requirements and constraints", "agent": "researcher", "priority": 10},
                {"description": "Create high-level architecture", "agent": "planner", "priority": 9},
                {"description": "Design detailed components", "agent": "planner", "priority": 8},
                {"description": "Generate design documents", "agent": "synthesizer", "priority": 7},
            ],
            "general": [
                {"description": "Analyze task requirements", "agent": "planner", "priority": 10},
                {"description": "Execute primary task", "agent": "executor", "priority": 8},
                {"description": "Review and finalize", "agent": "synthesizer", "priority": 6},
            ],
        }

        base_tasks = templates.get(goal_type, templates["general"])

        # Generate subtasks with IDs and dependencies
        for i, template in enumerate(base_tasks):
            task = Subtask(
                id=i + 1,
                description=template["description"],
                agent=template["agent"],
                priority=float(template["priority"]),
                blocked_by=[i] if i > 0 else [],  # Depends on previous task
                estimated_duration=self._estimate_task_duration(template["description"]),
            )
            subtasks.append(task)

        return subtasks[:self.max_subtasks]

    def _estimate_task_duration(self, description: str) -> str:
        """Estimate duration for a task."""
        desc_lower = description.lower()

        if any(k in desc_lower for k in ["review", "define", "understand", "analyze"]):
            return "30 minutes"
        elif any(k in desc_lower for k in ["implement", "create", "build", "gather"]):
            return "2 hours"
        elif any(k in desc_lower for k in ["test", "validate", "review"]):
            return "1 hour"
        elif any(k in desc_lower for k in ["synthesize", "generate", "document"]):
            return "1 hour"
        elif any(k in desc_lower for k in ["setup", "configure"]):
            return "30 minutes"
        else:
            return "1 hour"

    def _build_dependency_graph(self, subtasks: List[Subtask]) -> Dict:
        """Build a dependency graph for the subtasks."""
        graph = {}

        for task in subtasks:
            graph[task.id] = {
                "depends_on": task.blocked_by,
                "blocks": [],  # Will be populated below
            }

        # Populate blocks (reverse of depends_on)
        for task in subtasks:
            for dep_id in task.blocked_by:
                if dep_id in graph:
                    graph[dep_id]["blocks"].append(task.id)

        return graph

    def _assign_priorities(self, subtasks: List[Subtask], dependency_graph: Dict) -> List[Subtask]:
        """Assign priorities considering dependencies."""
        # Calculate critical path priority boost
        for task in subtasks:
            # Tasks with more dependents get priority boost
            dependents = len(dependency_graph.get(task.id, {}).get("blocks", []))
            dependency_boost = dependents * 0.5

            # Adjust priority
            task.priority = min(10.0, task.priority + dependency_boost)
            task.priority = round(task.priority, 1)

        return sorted(subtasks, key=lambda t: -t.priority)

    def _identify_risks(self, subtasks: List[Subtask], constraints: dict) -> list:
        """Identify potential risks in the plan."""
        risks = []

        # Check for tight deadlines
        if constraints.get("time_urgency") == "high":
            risks.append({
                "type": "schedule",
                "description": "Tight deadline may affect quality",
                "mitigation": "Prioritize core functionality",
                "severity": "high",
            })

        # Check for long dependency chains
        max_chain = self._find_longest_chain(subtasks)
        if max_chain > 7:
            risks.append({
                "type": "complexity",
                "description": f"Long dependency chain ({max_chain} tasks)",
                "mitigation": "Consider parallel execution where possible",
                "severity": "medium",
            })

        # Check for limited quality constraint
        if constraints.get("quality") == "high" and constraints.get("time_urgency") == "high":
            risks.append({
                "type": "scope",
                "description": "High quality + urgent timeline may conflict",
                "mitigation": "Focus on must-have deliverables",
                "severity": "high",
            })

        # Check for high complexity
        if constraints.get("complexity") == "high":
            risks.append({
                "type": "complexity",
                "description": "High complexity task",
                "mitigation": "Break into smaller subtasks if possible",
                "severity": "medium",
            })

        return risks

    def _find_longest_chain(self, subtasks: List[Subtask]) -> int:
        """Find the longest dependency chain."""
        graph = {t.id: t.blocked_by for t in subtasks}

        def chain_length(task_id, visited=None):
            if visited is None:
                visited = set()

            if task_id in visited:
                return 0

            visited.add(task_id)
            deps = graph.get(task_id, [])
            if not deps:
                return 1

            return 1 + max(chain_length(dep, visited.copy()) for dep in deps)

        return max(chain_length(t.id) for t in subtasks) if subtasks else 0

    def _estimate_duration(self, subtasks: List[Subtask]) -> str:
        """Estimate total plan duration."""
        # Calculate based on parallel execution (tasks that can run concurrently)
        max_parallel_time = 0
        current_time = 0

        # Simple estimation: sum all task durations
        for task in subtasks:
            dur_str = task.estimated_duration
            if "minute" in dur_str:
                minutes = int(dur_str.split()[0])
                current_time += minutes
            elif "hour" in dur_str:
                hours = int(dur_str.split()[0])
                current_time += hours * 60

        if current_time >= 60:
            hours = current_time // 60
            return f"{hours} hour{'s' if hours > 1 else ''}"
        else:
            return f"{current_time} minutes"

    def _generate_plan_summary(self, subtasks: List[Subtask]) -> str:
        """Generate a human-readable plan summary."""
        summary = f"Plan with {len(subtasks)} subtasks:\n"

        for task in subtasks[:5]:
            summary += f"- [{task.priority}] {task.description} ({task.agent})\n"

        if len(subtasks) > 5:
            summary += f"- ... and {len(subtasks) - 5} more\n"

        return summary


if __name__ == "__main__":
    # Test the planner agent
    async def test():
        agent = PlannerAgent()

        result = await agent.execute({
            "goal": "Competitive analysis of AI coding assistants in 2026",
            "constraints": {"time": "1 week"},
            "research_output": {"findings": []},
        })

        print(f"Plan ID: {result['plan_id']}")
        print(f"Subtasks: {len(result['subtasks'])}")
        print(f"Summary: {result['summary']}")

    asyncio.run(test())
