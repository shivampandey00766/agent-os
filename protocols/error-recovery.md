# Error Recovery Protocol

Protocol for handling failures, retries, and dead-letter queue processing.

## Retry Strategy

### Exponential Backoff

When a task fails, retry with exponential backoff:

```
delay = base_delay * (2 ^ attempt_count) + jitter
```

| Attempt | Base Delay (5s) | Actual Delay (with ±1s jitter) |
|---------|-----------------|--------------------------------|
| 1 | 5s | 4-6s |
| 2 | 10s | 9-11s |
| 3 | 20s | 19-21s |
| 4 | 40s | 39-41s |
| 5 | 80s | 79-81s |

### Retry Configuration

```python
RETRY_CONFIG = {
    "base_delay": 5,        # seconds
    "max_delay": 300,       # 5 minutes max
    "max_attempts": 3,      # attempts before dead letter
    "jitter": True,         # add randomness
    "jitter_range": 1,       # ±1 second
}
```

## Dead Letter Queue

Tasks that exceed `max_attempts` are moved to the dead letter queue.

### Dead Letter Entry Schema

```json
{
  "id": "task-uuid",
  "original_task": {...},
  "error_history": [
    {"attempt": 1, "error": "Network timeout", "timestamp": "..."},
    {"attempt": 2, "error": "Connection refused", "timestamp": "..."},
    {"attempt": 3, "error": "Service unavailable", "timestamp": "..."}
  ],
  "failed_at": "2026-03-27T10:30:00Z",
  "failure_reason": "MAX_ATTEMPTS_EXCEEDED",
  "manual_review_required": true
}
```

### Dead Letter Processing

1. **Immediate**: Log the failure with full error history
2. **Alert**: Notify relevant handlers (optional)
3. **Store**: Keep in dead_letter queue for analysis
4. **Metrics**: Update failure metrics

## Error Categories

| Category | Examples | Recovery Action |
|----------|----------|----------------|
| **Transient** | Network timeout, rate limit | Retry with backoff |
| **Resource** | Out of memory, disk full | Retry after cleanup |
| **Validation** | Invalid input, missing params | Fail fast, no retry |
| **Auth** | Token expired, permission denied | Refresh auth, retry |
| **External** | API down, service unavailable | Retry with longer delay |
| **Internal** | Code bug, assertion failure | Log, no retry, escalate |

## Recovery Patterns

### 1. Retry with Circuit Breaker

```python
class CircuitBreaker:
    """Prevents cascading failures by stopping retries after threshold."""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpen("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        self.failures = 0
        self.state = "CLOSED"

    def _on_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
```

### 2. Fallback Chaining

```python
class FallbackChain:
    """Try multiple implementations in sequence."""

    def __init__(self):
        self.handlers = []

    def add_handler(self, handler, priority: int = 0):
        self.handlers.append((priority, handler))
        self.handlers.sort(key=lambda x: -x[0])  # Higher priority first

    def execute(self, input_data: dict) -> dict:
        errors = []
        for priority, handler in self.handlers:
            try:
                return handler(input_data)
            except Exception as e:
                errors.append({"handler": handler.__name__, "error": str(e)})
                continue

        return {
            "error": "ALL_HANDLERS_FAILED",
            "details": errors,
        }
```

### 3. Checkpoint Resume

```python
class CheckpointRecovery:
    """Recover from failures using saved checkpoints."""

    def __init__(self, checkpoint_manager: CheckpointManager):
        self.checkpoint_manager = checkpoint_manager

    def recover(self, task_id: str) -> Optional[dict]:
        """Attempt to recover task from checkpoint."""
        progress = self.checkpoint_manager.get_task_progress(task_id)

        if not progress:
            return None

        # Determine where to resume
        if progress.steps_completed:
            next_step = progress.steps_pending[0] if progress.steps_pending else None
            return {
                "resume_from": next_step,
                "completed_steps": progress.steps_completed,
                "context": progress.output_preview,
            }

        return None
```

## Error Response Format

All errors should follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {},
    "recoverable": true,
    "retry_after": 5,
    "incident_id": "uuid"
  }
}
```

## Metrics

Track these metrics for error analysis:

| Metric | Description | Alert Threshold |
|--------|-------------|------------------|
| `error_rate` | Percentage of failed tasks | > 5% |
| `retry_rate` | Retries / total attempts | > 20% |
| `dead_letter_rate` | DLQ entries / total | > 2% |
| `mean_time_to_recovery` | Average recovery time | > 60s |
| `circuit_breaker_open` | Circuit breaker activations | > 1/hour |

## Health Checks

Regular health checks to detect issues:

```python
def health_check():
    """Run periodic health checks."""
    checks = {
        "queue_depth": get_queue_stats()["pending"] < 100,
        "dead_letter_ratio": get_dead_letter_ratio() < 0.1,
        "checkpoint_age": get_last_checkpoint_age() < 300,  # 5 minutes
        "memory_usage": get_memory_usage() < 0.9,
    }

    healthy = all(checks.values())
    return {
        "healthy": healthy,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
    }
```
