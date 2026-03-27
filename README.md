# Agent OS

Deep research autonomous agent system built on Claude Code's infrastructure. Capable of researching any topic, planning tasks, executing implementations, and self-improving from feedback.

## Features

- **Multi-Agent Orchestration**: RESEARCHER → PLANNER → EXECUTOR → SYNTHESIZER chain
- **4-Layer Memory**: Working, Episodic, Semantic, Procedural
- **Task Queue**: File-based with atomic operations, retry logic, dead-letter handling
- **Checkpointing**: State persistence for resume capability
- **Self-Improvement**: Learns from execution feedback

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     AGENT OS (SKILL.md)                      │
├──────────────────────────────────────────────────────────────┤
│  RESEARCHER ──► PLANNER ──► EXECUTOR ──► SYNTHESIZER       │
├──────────────────────────────────────────────────────────────┤
│                      ORCHESTRATOR                             │
│         OBSERVE → REASON → ACT → CHECKPOINT                 │
├──────────────────────────────────────────────────────────────┤
│                      KERNEL                                   │
│  TaskQueue │ Checkpoint │ Memory │ SelfImprover             │
├──────────────────────────────────────────────────────────────┤
│                   4-LAYER MEMORY                             │
│  Working │ Episodic │ Semantic │ Procedural                  │
└──────────────────────────────────────────────────────────────┘
```

## Installation

```bash
cd agent-os
```

No external dependencies required - uses Python standard library.

## Usage

### CLI

```bash
# Run a research task
python agent_os_cli.py research "AI coding assistants competitive landscape 2026"

# Check queue status
python agent_os_cli.py status

# Enqueue a custom task
python agent_os_cli.py enqueue research --query "your topic"

# Run orchestrator to process queued tasks
python agent_os_cli.py run
```

### Python API

```python
import asyncio
from kernel.orchestrator import Orchestrator

async def main():
    orchestrator = Orchestrator()
    result = await orchestrator.run(initial_task={
        "type": "research",
        "input": {"query": "your topic", "depth": "comprehensive"},
        "priority": 10
    })
    print(result)

asyncio.run(main())
```

## Components

### Kernel

| Component | File | Description |
|-----------|------|-------------|
| Task Queue | `kernel/task_queue.py` | File-based JSON queue with retry/dead-letter |
| Checkpoint | `kernel/checkpoint.py` | State persistence for resume |
| Memory | `kernel/memory.py` | 4-layer memory system |
| Self-Improver | `kernel/self_improver.py` | Learning from execution feedback |

### Agents

| Agent | File | Description |
|-------|------|-------------|
| Researcher | `agents/researcher/researcher_agent.py` | Deep web research |
| Planner | `agents/planner/planner_agent.py` | Task decomposition |
| Executor | `agents/executor/executor_agent.py` | Code generation |
| Synthesizer | `agents/synthesizer/synthesizer_agent.py` | Report generation |

### Memory Layers

| Layer | Purpose | Retention |
|-------|---------|-----------|
| Working | Current session context | Session only |
| Episodic | Past interactions | 30 days |
| Semantic | Knowledge base | Permanent |
| Procedural | Learned skills | Permanent |

## Testing

```bash
# Phase 1 verification
python test_phase1.py

# Research task test
python test_research_task.py

# Self-improvement test
python test_self_improver.py

# Full integration
python test_full_integration.py
```

## Project Structure

```
agent-os/
├── SKILL.md                    # Root skill
├── agent_os_cli.py            # CLI interface
├── kernel/                    # Core kernel
│   ├── task_queue.py          # Task queue
│   ├── checkpoint.py          # Checkpoint system
│   ├── memory.py              # 4-layer memory
│   ├── orchestrator.py        # Main agent loop
│   ├── self_improver.py       # Self-improvement
│   └── skill_loader.py        # Skill loader
├── agents/                    # Agent implementations
│   ├── researcher/
│   ├── planner/
│   ├── executor/
│   └── synthesizer/
├── protocols/                 # Handoff and error protocols
├── skills/                   # Available skills
├── queue/                    # Task queue files
│   ├── pending/
│   ├── in_progress/
│   ├── completed/
│   └── dead_letter/
├── memory/                   # Memory files
│   ├── working/
│   ├── episodic/
│   ├── semantic/
│   └── procedural/
└── test_*.py               # Test files
```

## Protocols

### Handoff Protocol
Agent handoff format: `[INVOKE:agent|input]`

### Error Recovery
- Automatic retry with exponential backoff
- Dead letter queue for failed tasks
- Checkpoint-based resume

## Example Output

```
=================================================================
                    AGENT OS v1.0
          Deep Research Autonomous Agent System
=================================================================

[CLI] Starting research: AI coding assistants competitive landscape 2026

--- Iteration 1 ---
[OBSERVE] Task: research | Priority: 10
[REASON] Agent: research
[REASON] Plan: 4 steps
[ACT] Executing with research agent...

[ORCHESTRATOR] Task completed successfully

FINAL REPORT
=================================================================
Executive Summary: AI Coding Assistants Competitive Landscape 2026

Key Findings:
- GitHub Copilot leads with 40% market share
- Claude Code showing fastest growth (300% enterprise adoption)
- Competition intensifying with focus on collaboration features

Top Recommendation: Invest in Claude Code integration for enterprise workflows.
=================================================================
```

## License

MIT
