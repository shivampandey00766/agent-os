# Agent Handoff Protocol

Protocol for transferring work between agents in the Agent OS multi-agent system.

## Handoff Format

```
[INVOKE:<agent_type>|<input_data>]
```

## Agent Types

| Agent | Type String | Purpose |
|-------|-------------|---------|
| Researcher | `researcher` | Deep web research |
| Planner | `planner` | Task decomposition |
| Executor | `executor` | Code implementation |
| Synthesizer | `synthesizer` | Report generation |

## Handoff Chain

```
RESEARCHER → PLANNER → EXECUTOR → SYNTHESIZER
     ↓           ↓          ↓          ↓
   Memory      Memory     Memory     Output
```

## Invocation Examples

### Researcher → Planner Handoff
```
[INVOKE:planner|{
  "research_output": {
    "findings": ["Source 1: LLM trends", "Source 2: AI agents growth"],
    "confidence": 0.85,
    "sources": ["perplexity", "firecrawl"]
  },
  "task_goal": "Competitive analysis of AI coding assistants"
}]
```

### Planner → Executor Handoff
```
[INVOKE:executor|{
  "subtasks": [
    {"id": 1, "description": "Gather competitor list", "priority": 10, "blocked_by": []},
    {"id": 2, "description": "Analyze features", "priority": 8, "blocked_by": [1]},
    {"id": 3, "description": "Generate comparison matrix", "priority": 6, "blocked_by": [2]}
  ],
  "constraints": {"budget": "limited", "time": "2 weeks"}
}]
```

### Executor → Synthesizer Handoff
```
[INVOKE:synthesizer|{
  "implementation_output": {
    "comparison_matrix": {...},
    "feature_analysis": {...},
    "recommendations": ["优先考虑 A", "B 的性价比高"]
  },
  "format": "executive_summary"
}]
```

## Loop Prevention

The handoff system includes loop detection:

1. **Visited Set**: Track agent IDs that have been visited
2. **Max Hops**: Limit chain length to prevent infinite loops
3. **Duplicate Detection**: Detect if same agent invoked twice with similar input

### Implementation

```python
class HandoffManager:
    """Manages agent handoffs with loop prevention."""

    def __init__(self, max_hops: int = 10):
        self.max_hops = max_hops
        self.handoff_log: list = []

    def invoke(
        self,
        agent_type: str,
        input_data: dict,
        context: dict = None
    ) -> dict:
        """Invoke an agent with loop prevention."""

        # Check for loops
        visited = context.get("visited_agents", []) if context else []
        if len(visited) >= self.max_hops:
            return {
                "error": "MAX_HOPS_EXCEEDED",
                "message": f"Chain exceeded {self.max_hops} hops",
                "visited": visited,
            }

        # Check for duplicate agents in chain
        if agent_type in visited:
            return {
                "error": "LOOP_DETECTED",
                "message": f"Agent {agent_type} already visited",
                "visited": visited,
            }

        # Log handoff
        handoff = {
            "from": visited[-1] if visited else "initiator",
            "to": agent_type,
            "input_size": len(str(input_data)),
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.handoff_log.append(handoff)

        # Execute agent
        new_visited = visited + [agent_type]
        result = self._execute_agent(
            agent_type,
            input_data,
            {**(context or {}), "visited_agents": new_visited}
        )

        return result
```

## Error Handling

| Error | Meaning | Recovery |
|-------|---------|----------|
| `MAX_HOPS_EXCEEDED` | Chain too long | Return partial results |
| `LOOP_DETECTED` | Circular handoff | Abort chain |
| `AGENT_NOT_FOUND` | Unknown agent type | Fall back to generic |
| `AGENT_TIMEOUT` | Agent took too long | Retry with backup |

## Handoff Best Practices

1. **Pass Context Forward**: Include relevant context from previous agents
2. **Maintain Visited Set**: Track the chain for debugging
3. **Set Max Hops**: Prevent runaway chains
4. **Log All Handoffs**: Record for episodic memory
5. **Handle Partial Results**: If an agent fails, pass what was completed
