# Agent OS Orchestrator

The orchestrator is the main agent loop that drives autonomous operation through a continuous OBSERVE → REASON → ACT → CHECKPOINT cycle.

## Agent Loop

```
┌─────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR LOOP                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────────┐   │
│   │ OBSERVE │───▶│ REASON │───▶│   ACT   │───▶│ CHECKPOINT  │   │
│   └─────────┘    └─────────┘    └─────────┘    └──────┬──────┘   │
│        ▲                                               │         │
│        └───────────────────────────────────────────────┘         │
│                         (loop until complete)                    │
└─────────────────────────────────────────────────────────────────┘
```

## Phase Details

### OBSERVE
Gather current state from all sources:
- Check task queue for pending tasks
- Read current checkpoint state
- Query memory layers (working, episodic, semantic, procedural)
- Monitor external events (MCP server notifications)

**State Captured:**
- Current task and its requirements
- Available context from memory
- System resource status
- External signals

### REASON
Analyze and plan:
- Interpret task requirements
- Check dependencies and blocked tasks
- Identify relevant skills from procedural memory
- Determine optimal action sequence
- Assess confidence and risk

**Reasoning Outputs:**
- Action plan with steps
- Resource requirements
- Potential failure modes
- Expected outcomes

### ACT
Execute the planned actions:
- Invoke appropriate agents (researcher, planner, executor, synthesizer)
- Call MCP tools (GitHub, browser, filesystem, etc.)
- Generate code or content
- Update memory with findings
- Communicate with user or other agents

**Action Types:**
- `research`: Deep web research using WebSearch, WebFetch, BrowserMCP
- `plan`: Task decomposition into subtasks
- `execute`: Code generation and implementation
- `synthesize`: Aggregate results into reports

### CHECKPOINT
Persist state for resume capability:
- Save current progress to checkpoint
- Update task status in queue
- Commit episodic memory
- Update semantic knowledge base
- Log metrics (time, success rate)

## Orchestrator Implementation

```python
class Orchestrator:
    """
    Main agent loop orchestrator.
    Runs OBSERVE → REASON → ACT → CHECKPOINT until task completion.
    """

    def __init__(self, config: OrchestratorConfig):
        self.task_queue = TaskQueue(config.queue_path)
        self.checkpoint_manager = CheckpointManager(config.checkpoint_path)
        self.memory = MemoryManager(config.memory_path)
        self.skill_loader = SkillLoader()

        self.agents = {
            "researcher": ResearcherAgent(),
            "planner": PlannerAgent(),
            "executor": ExecutorAgent(),
            "synthesizer": SynthesizerAgent(),
        }

        self.current_phase = "observe"
        self.session_id = str(uuid.uuid4())

    def run(self, initial_task: Task = None):
        """Main orchestrator loop."""

        # Create initial checkpoint
        self.checkpoint_manager.create_checkpoint(
            session_id=self.session_id,
            current_task_id=initial_task.id if initial_task else None
        )

        # If no initial task, try to dequeue one
        if not initial_task:
            initial_task = self.task_queue.dequeue()

        task = initial_task
        max_iterations = 100
        iteration = 0

        while task and iteration < max_iterations:
            iteration += 1

            # OBSERVE
            self.checkpoint_manager.update_phase("observe")
            state = self._observe(task)
            self.log(f"Observed state: {state['summary']}")

            # REASON
            self.checkpoint_manager.update_phase("reason")
            plan = self._reason(task, state)
            self.log(f"Reasoned plan: {plan['summary']}")

            # ACT
            self.checkpoint_manager.update_phase("act")
            result = self._act(task, plan)
            self.log(f"Action result: {result['summary']}")

            # CHECKPOINT
            self.checkpoint_manager.update_phase("checkpoint")
            self._checkpoint(task, result)

            # Check if task is complete
            if result.get("complete"):
                self.task_queue.complete(task.id, result["output"])
                self.checkpoint_manager.complete()
                break

            # Handle failure
            if result.get("failed"):
                if task.attempt_count >= task.max_attempts:
                    self.task_queue.fail(task.id, result["error"])
                    self.checkpoint_manager.complete()
                else:
                    self.task_queue.fail(task.id, result["error"])
                break

            # Get next task
            task = self.task_queue.dequeue()

        return {"status": "completed", "iterations": iteration}

    def _observe(self, task: Task) -> dict:
        """Observe current state for the task."""
        return {
            "task": task,
            "context": self.memory.get_working_context(),
            "similar_past": self.memory.query_similar(task.input.get("query", "")),
            "skills_available": self.skill_loader.get_available_skills(),
            "queue_depth": self.task_queue.get_queue_stats(),
        }

    def _reason(self, task: Task, state: dict) -> dict:
        """Reason about how to handle the task."""
        agent_type = task.type  # research, plan, execute, synthesize

        return {
            "agent": agent_type,
            "steps": self._decompose_task(task, agent_type),
            "confidence": 0.85,
            "expected_duration": "5-10 minutes",
        }

    def _act(self, task: Task, plan: dict) -> dict:
        """Execute the planned actions."""
        agent = self.agents.get(task.type)
        if not agent:
            return {"failed": True, "error": f"Unknown task type: {task.type}"}

        try:
            result = agent.execute(task.input, context={
                "steps": plan["steps"],
                "checkpoint_manager": self.checkpoint_manager,
                "memory": self.memory,
            })

            return {
                "complete": True,
                "output": result,
            }
        except Exception as e:
            return {
                "failed": True,
                "error": str(e),
            }

    def _checkpoint(self, task: Task, result: dict):
        """Save checkpoint with current progress."""
        self.checkpoint_manager.update_checkpoint(
            updates={
                "current_task_id": task.id,
                "task_progress": {
                    "status": "completed" if result.get("complete") else "failed",
                    "output_size": len(str(result.get("output", ""))),
                }
            }
        )

    def _decompose_task(self, task: Task, agent_type: str) -> list:
        """Decompose task into steps based on agent type."""
        decompositions = {
            "research": [
                "Analyze query and formulate search strategy",
                "Execute parallel web searches",
                "Extract and validate content from sources",
                "Synthesize findings with confidence scoring",
            ],
            "plan": [
                "Understand end goal from research",
                "Identify dependencies and constraints",
                "Break down into ordered subtasks",
                "Assign priorities and resources",
            ],
            "execute": [
                "Review implementation plan",
                "Set up development environment",
                "Implement code/features",
                "Run tests and validate",
            ],
            "synthesize": [
                "Gather outputs from all agents",
                "Identify key insights and patterns",
                "Structure final deliverable",
                "Add executive summary and recommendations",
            ],
        }
        return decompositions.get(agent_type, ["Generic task step"])
```

## Error Recovery

The orchestrator handles failures through:

1. **Retry Logic**: Tasks can be retried up to `max_attempts`
2. **Dead Letter Queue**: Tasks exceeding retries go to dead_letter for manual review
3. **Checkpoint Resume**: Can resume from last checkpoint on restart
4. **Graceful Degradation**: If an agent fails, can try alternative approach

## Multi-Agent Coordination

When a task requires multiple agents:

```
User Request
     │
     ▼
RESEARCHER ──────┐
     │           │
     ▼           │
PLANNER ◀────────┘
     │
     ▼
EXECUTOR
     │
     ▼
SYNTHESIZER ─────┐
     │           │
     ▼           ▼
  Memory     User Output
```

Each agent:
- Receives input from previous agent
- Produces output for next agent
- Reports progress to checkpoint
- Updates memory with findings
