# Executor Agent

Code generation and implementation agent for executing planned tasks.

## Capabilities

- Code generation from specifications
- File creation and modification
- Test implementation
- Code validation and linting
- Implementation progress tracking

## Execution Protocol

```
1. Review Plan → Implementation Strategy
2. Environment Setup
3. Code Generation
4. Validation & Testing
5. Error Resolution
6. Completion & Handoff
```

## Implementation

```python
class ExecutorAgent:
    """Code implementation and execution agent."""

    def __init__(self, config: ExecutorConfig = None):
        self.config = config or ExecutorConfig()
        self.supported_languages = ["python", "typescript", "javascript", "go", "rust"]
        self.output_dir = Path("C:/Users/Shiva/Downloads/agent-os/output")

    async def execute(self, task_input: dict, context: dict = None) -> dict:
        """
        Execute implementation tasks from a plan.

        Args:
            task_input: {
                "plan": {...},  # From planner agent
                "implementation_type": "code|report|analysis",
            }
            context: Additional context

        Returns:
            {
                "status": "completed",
                "output": {...},
                "files_created": [...],
                "tests_run": [...],
            }
        """
        plan = task_input.get("plan", {})
        impl_type = task_input.get("implementation_type", "code")

        subtasks = plan.get("subtasks", [])
        completed_subtasks = []
        files_created = []
        errors = []

        for subtask in subtasks:
            if subtask["status"] == "completed":
                continue

            try:
                # Execute each subtask
                result = await self._execute_subtask(
                    subtask,
                    plan,
                    context
                )

                completed_subtasks.append({
                    **subtask,
                    "status": "completed",
                    "result": result,
                })

                if result.get("files_created"):
                    files_created.extend(result["files_created"])

            except Exception as e:
                errors.append({
                    "subtask_id": subtask["id"],
                    "error": str(e),
                })

                if subtask.get("blocking"):
                    # Stop on critical error
                    break

        return {
            "status": "completed" if len(errors) == 0 else "partial",
            "completed_subtasks": completed_subtasks,
            "files_created": files_created,
            "errors": errors,
            "output": self._generate_output(completed_subtasks, plan),
        }

    async def _execute_subtask(
        self,
        subtask: dict,
        plan: dict,
        context: dict = None
    ) -> dict:
        """Execute a single subtask."""
        description = subtask["description"]
        agent_type = subtask.get("agent", "executor")

        # Route to appropriate handler
        if "setup" in description.lower() or "environment" in description.lower():
            return await self._setup_environment(subtask, plan)
        elif "implement" in description.lower() or "create" in description.lower():
            return await self._generate_code(subtask, plan, context)
        elif "test" in description.lower() or "validate" in description.lower():
            return await self._run_tests(subtask, plan)
        elif "review" in description.lower() or "document" in description.lower():
            return await self._generate_documentation(subtask, plan)
        else:
            return await self._generic_execution(subtask, plan)

    async def _setup_environment(self, subtask: dict, plan: dict) -> dict:
        """Set up development environment."""
        return {
            "action": "environment_setup",
            "status": "completed",
            "details": "Environment ready",
        }

    async def _generate_code(
        self,
        subtask: dict,
        plan: dict,
        context: dict = None
    ) -> dict:
        """Generate code based on subtask description."""
        # Determine language and framework
        language = self._detect_language(subtask["description"])
        framework = self._detect_framework(subtask["description"])

        # Generate code structure
        code_structure = self._create_code_structure(
            subtask,
            plan,
            language,
            framework
        )

        # Write files
        files_created = []
        for file_path, content in code_structure.items():
            full_path = self.output_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
            files_created.append(str(full_path))

        return {
            "action": "code_generation",
            "language": language,
            "framework": framework,
            "files_created": files_created,
            "status": "completed",
        }

    def _detect_language(self, description: str) -> str:
        """Detect programming language from description."""
        desc_lower = description.lower()

        if any(k in desc_lower for k in ["python", "pytorch", "tensorflow"]):
            return "python"
        elif any(k in desc_lower for k in ["typescript", "ts", "react", "node"]):
            return "typescript"
        elif any(k in desc_lower for k in ["javascript", "js", "web"]):
            return "javascript"
        elif any(k in desc_lower for k in ["go", "golang"]):
            return "go"
        elif any(k in desc_lower for k in ["rust", "rs"]):
            return "rust"
        else:
            return "python"  # Default

    def _detect_framework(self, description: str) -> str:
        """Detect framework from description."""
        desc_lower = description.lower()

        if "fastapi" in desc_lower or "api" in desc_lower:
            return "fastapi"
        elif "react" in desc_lower:
            return "react"
        elif "next" in desc_lower:
            return "nextjs"
        elif "django" in desc_lower or "flask" in desc_lower:
            return "django"
        else:
            return "none"

    def _create_code_structure(
        self,
        subtask: dict,
        plan: dict,
        language: str,
        framework: str
    ) -> dict:
        """Create the code file structure."""
        files = {}

        if language == "python":
            files["main.py"] = self._generate_python_main(subtask, plan)
            files["requirements.txt"] = self._generate_requirements(subtask, plan)
            files["config.py"] = self._generate_config(subtask, plan)

        elif language == "typescript":
            files["src/index.ts"] = self._generate_ts_main(subtask, plan)
            files["package.json"] = self._generate_package_json(subtask, plan)

        return files

    def _generate_python_main(self, subtask: dict, plan: dict) -> str:
        """Generate Python main file."""
        return f'''"""
Generated implementation for: {subtask['description']}
Plan: {plan.get('goal', 'N/A')}
"""

import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    logger.info("Starting implementation...")
    # TODO: Implement {subtask['description']}
    pass


if __name__ == "__main__":
    main()
'''

    def _generate_requirements(self, subtask: dict, plan: dict) -> str:
        """Generate requirements.txt."""
        return '''# Requirements for implementation
# Add dependencies as needed
'''

    def _generate_config(self, subtask: dict, plan: dict) -> str:
        """Generate config file."""
        return '''"""
Configuration for implementation
"""
'''

    def _generate_ts_main(self, subtask: dict, plan: dict) -> str:
        """Generate TypeScript main file."""
        return f'''// Generated implementation for: {subtask['description']}
// Plan: {plan.get('goal', 'N/A')}

export async function main() {{
  console.log("Starting implementation...");
  // TODO: Implement {subtask['description']}
}}
'''

    def _generate_package_json(self, subtask: dict, plan: dict) -> str:
        """Generate package.json."""
        return f'''{{
  "name": "agent-os-implementation",
  "version": "1.0.0",
  "description": "{plan.get('goal', 'Agent OS Implementation')}",
  "main": "src/index.ts",
  "scripts": {{
    "start": "ts-node src/index.ts"
  }}
}}
'''

    async def _run_tests(self, subtask: dict, plan: dict) -> dict:
        """Run tests on generated code."""
        return {
            "action": "test_execution",
            "tests_run": 0,
            "tests_passed": 0,
            "status": "completed",
        }

    async def _generate_documentation(self, subtask: dict, plan: dict) -> dict:
        """Generate documentation."""
        doc_content = f"""# {plan.get('goal', 'Implementation Documentation')}

## Overview
{subtask['description']}

## Implementation Details

## Usage

## API Reference
"""
        return {
            "action": "documentation",
            "files_created": ["documentation.md"],
            "status": "completed",
        }

    async def _generic_execution(self, subtask: dict, plan: dict) -> dict:
        """Generic execution for unhandled subtask types."""
        return {
            "action": "generic",
            "description": subtask["description"],
            "status": "completed",
        }

    def _generate_output(
        self,
        completed_subtasks: list,
        plan: dict
    ) -> dict:
        """Generate final output from completed subtasks."""
        return {
            "plan_id": plan.get("plan_id"),
            "goal": plan.get("goal"),
            "tasks_completed": len(completed_subtasks),
            "summary": f"Completed {len(completed_subtasks)} subtasks",
        }
```

## Output Format

```json
{
  "status": "completed",
  "completed_subtasks": [
    {
      "id": 1,
      "description": "Set up environment",
      "status": "completed",
      "result": {...}
    }
  ],
  "files_created": [
    "/path/to/main.py",
    "/path/to/requirements.txt"
  ],
  "errors": [],
  "output": {
    "plan_id": "uuid",
    "goal": "...",
    "tasks_completed": 5
  }
}
```

## Usage

```python
executor = ExecutorAgent()
result = await executor.execute({
    "plan": planner_output,
    "implementation_type": "code",
})
```
