---
name: agent-os
category: orchestration
description: Autonomous Agent OS with deep research, planning, and self-improvement capabilities
version: 1.0.0
author: Agent OS Team
---

# Agent OS

Deep research autonomous agent system built on Claude Code's infrastructure.

## Activation

```
/agent-os <task>
```

Example:
```
/agent-os Research the competitive landscape for AI coding assistants in 2026
```

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     AGENT OS (SKILL.md)                      │
│              Root skill that activates the OS                 │
├──────────────────────────────────────────────────────────────┤
│  RESEARCHER ──► PLANNER ──► EXECUTOR ──► SYNTHESIZER       │
├──────────────────────────────────────────────────────────────┤
│                      AGENT KERNEL                            │
│  Orchestrator │ Task Queue │ Memory │ Checkpointing          │
├──────────────────────────────────────────────────────────────┤
│                     MEMORY SYSTEM                            │
│  Working │ Episodic │ Semantic │ Procedural                  │
└──────────────────────────────────────────────────────────────┘
```

## Core Components

### Kernel (`kernel/`)
- **task_queue.py** - File-based JSON queue with atomic operations, retry logic, dead-letter handling
- **checkpoint.py** - State persistence for resume capability
- **memory.py** - 4-layer memory system (Working, Episodic, Semantic, Procedural)
- **orchestrator.py** - Main agent loop: OBSERVE → REASON → ACT → CHECKPOINT
- **skill_loader.py** - On-demand skill loading

### Agents (`agents/`)
- **researcher/** - Deep web research using WebSearch, WebFetch, BrowserMCP
- **planner/** - Task decomposition into subtasks
- **executor/** - Code generation and implementation
- **synthesizer/** - Result aggregation and report generation

### Memory Layers (`memory/`)
| Layer | Content | Retention |
|-------|---------|-----------|
| Working | Current session context | Session only |
| Episodic | Past interactions | 30 days |
| Semantic | Knowledge base, research | Permanent |
| Procedural | Learned skills, patterns | Permanent |

## Usage

### Direct Task
```
/agent-os Research AI trends in 2026
```

### With Parameters
```
/agent-os Research {query: "competitive landscape for AI coding assistants", depth: comprehensive}
```

### Via Python API
```python
from kernel.task_queue import TaskQueue, TaskType

queue = TaskQueue()
task = queue.enqueue(
    task_type=TaskType.RESEARCH.value,
    input_data={"query": "AI trends 2026"},
    priority=8
)
```

## Multi-Agent Chain

When activated, Agent OS runs:

1. **RESEARCHER** - Deep search using Perplexity, Firecrawl, Tavily
2. **PLANNER** - Break down into competitor analysis framework
3. **EXECUTOR** - Generate comparison matrix, store in semantic memory
4. **SYNTHESIZER** - Produce executive summary with recommendations

## Task Schema

```json
{
  "id": "uuid",
  "type": "research|plan|execute|synthesize",
  "status": "pending|in_progress|completed|failed|dead_letter",
  "priority": 1-10,
  "attempt_count": 0,
  "max_attempts": 3,
  "input": {...},
  "output": null,
  "error": null,
  "dependencies": [],
  "blocked_by": []
}
```

## Protocols

### Handoff Protocol
Agent handoff format: `[INVOKE:agent|input]`

### Error Recovery
- Automatic retry with exponential backoff
- Dead letter queue for failed tasks
- Checkpoint-based resume after failures

## Status

**Phase 1 Complete**: Core Kernel
- Task queue with atomic operations
- Checkpoint system for state persistence
- 4-layer memory system
- Orchestrator documentation

**Phase 2-5**: In progress
