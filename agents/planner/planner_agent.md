# Planner Agent

Task decomposition agent that breaks down complex goals into ordered subtasks with dependencies.

## Capabilities

- Goal analysis and decomposition
- Dependency graph construction
- Priority assignment
- Resource estimation
- Constraint identification

## Planning Protocol

```
1. Goal Analysis → End State Definition
2. Constraint Identification
3. Subtask Decomposition
4. Dependency Mapping
5. Priority Assignment
6. Plan Generation
```

## Implementation

```python
class PlannerAgent:
    """Task decomposition and planning agent."""

    def __init__(self, config: PlannerConfig = None):
        self.config = config or PlannerConfig()
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
                "available_agents": ["researcher", "executor"],
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
            context.get("available_agents", ["researcher", "planner", "executor", "synthesizer"])
        )

        # Step 4: Build dependency graph
        dependency_graph = self._build_dependency_graph(subtasks)

        # Step 5: Assign priorities
        prioritized = self._assign_priorities(subtasks, dependency_graph)

        # Step 6: Identify risks
        risks = self._identify_risks(prioritized, identified_constraints)

        return {
            "plan_id": str(uuid.uuid4()),
            "goal": goal,
            "goal_analysis": goal_analysis,
            "constraints": identified_constraints,
            "subtasks": prioritized,
            "dependency_graph": dependency_graph,
            "estimated_duration": self._estimate_duration(prioritized),
            "risks": risks,
            "summary": self._generate_plan_summary(prioritized),
        }

    def _analyze_goal(self, goal: str, research: dict = None) -> dict:
        """Analyze the goal to understand requirements."""
        keywords = goal.lower().split()

        # Identify goal type
        if any(k in keywords for k in ["create", "build", "implement", "make"]):
            goal_type = "implementation"
        elif any(k in keywords for k in ["research", "analyze", "investigate", "study"]):
            goal_type = "research"
        elif any(k in keywords for k in ["compare", "evaluate", "assess"]):
            goal_type = "evaluation"
        elif any(k in keywords for k in ["improve", "optimize", "enhance"]):
            goal_type = "improvement"
        else:
            goal_type = "general"

        # Identify key deliverables
        deliverables = self._extract_deliverables(goal)

        # Identify stakeholders/audience
        audience = self._extract_audience(goal)

        return {
            "type": goal_type,
            "deliverables": deliverables,
            "audience": audience,
            "complexity": self._estimate_complexity(goal, research),
        }

    def _extract_deliverables(self, goal: str) -> list:
        """Extract expected deliverables from goal."""
        deliverables = []

        if "report" in goal.lower():
            deliverables.append("report")
        if "analysis" in goal.lower():
            deliverables.append("analysis")
        if "code" in goal.lower() or "implement" in goal.lower():
            deliverables.append("code")
        if "recommendation" in goal.lower():
            deliverables.append("recommendations")
        if "comparison" in goal.lower():
            deliverables.append("comparison_matrix")

        return deliverables or ["outcome"]

    def _extract_audience(self, goal: str) -> str:
        """Extract target audience from goal."""
        goal_lower = goal.lower()

        if "executive" in goal_lower or "c-level" in goal_lower:
            return "executives"
        elif "technical" in goal_lower or "engineer" in goal_lower:
            return "technical"
        elif "customer" in goal_lower or "user" in goal_lower:
            return "end_users"
        else:
            return "general"

    def _estimate_complexity(self, goal: str, research: dict = None) -> str:
        """Estimate task complexity."""
        words = len(goal.split())

        # Check for complexity indicators
        has_comparison = "compare" in goal.lower() or "vs" in goal.lower()
        has_multiple_parts = "and" in goal.lower() or "," in goal
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
        time_patterns = [
            (r'(\d+)\s*day', 'days'),
            (r'(\d+)\s*week', 'weeks'),
            (r'(\d+)\s*hour', 'hours'),
            (r'urgent', 1),
            (r'asap', 1),
        ]

        for pattern, unit in time_patterns:
            import re
            match = re.search(pattern, goal_lower)
            if match:
                if isinstance(unit, int):
                    constraints["time_urgency"] = "high"
                else:
                    constraints["max_time"] = f"{match.group(1)} {unit}"
                break

        # Quality constraints
        if any(k in goal_lower for k in ["comprehensive", "thorough", "detailed"]):
            constraints["quality"] = "high"
        elif any(k in goal_lower for k in ["quick", "brief", "summary"]):
            constraints["quality"] = "standard"

        return constraints

    def _decompose(self, goal_analysis: dict, constraints: dict, agents: list) -> list:
        """Decompose goal into subtasks."""
        subtasks = []
        goal_type = goal_analysis["type"]

        # Task templates by type
        templates = {
            "implementation": [
                {"description": "Review requirements and design", "agent": "executor", "priority": 10},
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
        }

        base_tasks = templates.get(goal_type, templates["general"])

        # Generate subtasks with IDs and dependencies
        for i, template in enumerate(base_tasks):
            task = {
                "id": i + 1,
                "description": template["description"],
                "agent": template["agent"],
                "priority": template["priority"],
                "blocked_by": [i] if i > 0 else [],  # Depends on previous task
                "estimated_duration": self._estimate_task_duration(template["description"]),
                "status": "pending",
            }
            subtasks.append(task)

        return subtasks[:self.max_subtasks]

    def _estimate_task_duration(self, description: str) -> str:
        """Estimate duration for a task."""
        desc_lower = description.lower()

        if any(k in desc_lower for k in ["review", "define"]):
            return "30 minutes"
        elif any(k in desc_lower for k in ["implement", "gather"]):
            return "2 hours"
        elif any(k in desc_lower for k in ["test", "validate"]):
            return "1 hour"
        elif any(k in desc_lower for k in ["analyze", "synthesize"]):
            return "1 hour"
        else:
            return "1 hour"

    def _build_dependency_graph(self, subtasks: list) -> dict:
        """Build a dependency graph for the subtasks."""
        graph = {}

        for task in subtasks:
            task_id = task["id"]
            graph[task_id] = {
                "depends_on": task.get("blocked_by", []),
                "blocks": [],  # Will be populated below
            }

        # Populate blocks
        for task in subtasks:
            for dep_id in task.get("blocked_by", []):
                if dep_id in graph:
                    graph[dep_id]["blocks"].append(task["id"])

        return graph

    def _assign_priorities(self, subtasks: list, dependency_graph: dict) -> list:
        """Assign priorities considering dependencies."""
        # Calculate critical path priority boost
        for task in subtasks:
            # Tasks with more dependents get priority boost
            dependents = len(dependency_graph.get(task["id"], {}).get("blocks", []))
            dependency_boost = dependents * 0.5

            # Adjust priority
            task["priority"] = min(10, task["priority"] + dependency_boost)
            task["priority"] = round(task["priority"], 1)

        return sorted(subtasks, key=lambda t: -t["priority"])

    def _identify_risks(self, subtasks: list, constraints: dict) -> list:
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

        return risks

    def _find_longest_chain(self, subtasks: list) -> int:
        """Find the longest dependency chain."""
        graph = {t["id"]: t.get("blocked_by", []) for t in subtasks}

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

        return max(chain_length(t["id"]) for t in subtasks)

    def _estimate_duration(self, subtasks: list) -> str:
        """Estimate total plan duration."""
        # Sum durations of tasks not blocked by anything (parallelizable)
        # For simplicity, just sum all serial task durations
        durations = []
        current_time = 0

        for task in subtasks:
            dur_str = task.get("estimated_duration", "1 hour")
            # Parse duration (simplified)
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

    def _generate_plan_summary(self, subtasks: list) -> str:
        """Generate a human-readable plan summary."""
        summary = f"Plan with {len(subtasks)} subtasks:\n"

        for task in subtasks[:5]:
            summary += f"- [{task['priority']}] {task['description']} ({task['agent']})\n"

        if len(subtasks) > 5:
            summary += f"- ... and {len(subtasks) - 5} more\n"

        return summary
```

## Plan Output Format

```json
{
  "plan_id": "uuid",
  "goal": "Competitive analysis of AI coding assistants",
  "subtasks": [
    {
      "id": 1,
      "description": "Define evaluation criteria",
      "agent": "planner",
      "priority": 10,
      "blocked_by": [],
      "estimated_duration": "30 minutes",
      "status": "pending"
    },
    {
      "id": 2,
      "description": "Gather competitor data",
      "agent": "researcher",
      "priority": 9,
      "blocked_by": [1],
      "estimated_duration": "2 hours",
      "status": "pending"
    }
  ],
  "dependency_graph": {
    "1": {"depends_on": [], "blocks": [2]},
    "2": {"depends_on": [1], "blocks": []}
  },
  "estimated_duration": "4 hours",
  "risks": []
}
```

## Usage

```python
planner = PlannerAgent()
plan = await planner.execute({
    "goal": "Competitive analysis of AI coding assistants in 2026",
    "constraints": {"time": "1 week", "budget": "limited"},
    "research_output": researcher_output,
})
```
