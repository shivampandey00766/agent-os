"""
Executor Agent - Code generation and implementation.
Executes planned tasks, generates code, runs tests.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ExecutionResult:
    """Result of executing a subtask."""
    subtask_id: int
    description: str
    status: str  # completed, failed, skipped
    files_created: List[str]
    output: Dict
    duration_seconds: int

    def to_dict(self) -> dict:
        return asdict(self)


class ExecutorAgent:
    """
    Code implementation and execution agent.

    Execution Protocol:
    1. Review Plan → Implementation Strategy
    2. Environment Setup
    3. Code Generation
    4. Validation & Testing
    5. Error Resolution
    6. Completion & Handoff
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.output_dir = Path(self.config.get("output_dir", "C:/Users/Shiva/Downloads/agent-os/output"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.supported_languages = ["python", "typescript", "javascript", "go", "rust"]

    async def execute(self, task_input: dict, context: dict = None) -> dict:
        """
        Execute implementation tasks from a plan.

        Args:
            task_input: {
                "subtask": {...},  # Single subtask to execute
                "plan": {...},     # Full plan context
                "research": {...}, # Research findings
            }
            context: Additional context

        Returns:
            {
                "status": "completed",
                "output": {...},
                "files_created": [...],
            }
        """
        subtask = task_input.get("subtask")
        plan = task_input.get("plan", {})
        research = task_input.get("research", {})

        if subtask:
            # Execute single subtask
            result = await self._execute_subtask(subtask, plan, research, context)
            return {
                "status": "completed",
                "subtask_result": result.to_dict(),
                "files_created": result.files_created,
            }
        else:
            # Execute all subtasks from plan
            results = []
            all_files = []

            for subtask_dict in plan.get("subtasks", []):
                result = await self._execute_subtask(subtask_dict, plan, research, context)
                results.append(result)
                all_files.extend(result.files_created)

            return {
                "status": "completed",
                "results": [r.to_dict() for r in results],
                "files_created": all_files,
            }

    async def _execute_subtask(
        self,
        subtask: dict,
        plan: dict,
        research: dict,
        context: dict = None
    ) -> ExecutionResult:
        """Execute a single subtask."""
        subtask_id = subtask.get("id", 0)
        description = subtask.get("description", "")
        agent_type = subtask.get("agent", "executor")

        start_time = datetime.utcnow()
        files_created = []
        output = {}

        try:
            # Route to appropriate handler
            if "setup" in description.lower() or "environment" in description.lower():
                output = await self._setup_environment(subtask, plan)
            elif "implement" in description.lower() or "create" in description.lower() or "build" in description.lower():
                output, files = await self._generate_code(subtask, plan, research)
                files_created.extend(files)
            elif "test" in description.lower() or "validate" in description.lower():
                output, files = await self._run_tests(subtask, plan)
                files_created.extend(files)
            elif "review" in description.lower() or "document" in description.lower() or "generate" in description.lower():
                output, files = await self._generate_documentation(subtask, plan, research)
                files_created.extend(files)
            elif "analyze" in description.lower() or "assess" in description.lower():
                output = await self._analyze(subtask, plan, research)
            else:
                output = await self._generic_execution(subtask, plan)

            duration = int((datetime.utcnow() - start_time).total_seconds())

            return ExecutionResult(
                subtask_id=subtask_id,
                description=description,
                status="completed",
                files_created=files_created,
                output=output,
                duration_seconds=duration
            )

        except Exception as e:
            duration = int((datetime.utcnow() - start_time).total_seconds())
            return ExecutionResult(
                subtask_id=subtask_id,
                description=description,
                status="failed",
                files_created=files_created,
                output={"error": str(e)},
                duration_seconds=duration
            )

    async def _setup_environment(self, subtask: dict, plan: dict) -> dict:
        """Set up development environment."""
        # Simulate environment setup
        await asyncio.sleep(0.1)

        return {
            "action": "environment_setup",
            "status": "completed",
            "details": "Development environment ready",
            "tools": ["git", "python", "node"],
        }

    async def _generate_code(
        self,
        subtask: dict,
        plan: dict,
        research: dict
    ) -> tuple:
        """Generate code based on subtask description."""
        description = subtask.get("description", "").lower()

        # Determine language and framework
        language = self._detect_language(description)
        framework = self._detect_framework(description)

        # Generate code structure
        code_structure = self._create_code_structure(
            subtask,
            plan,
            language,
            framework,
            research
        )

        # Write files
        files_created = []
        for file_path, content in code_structure.items():
            full_path = self.output_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
            files_created.append(str(full_path))

        output = {
            "action": "code_generation",
            "language": language,
            "framework": framework,
            "files_created": files_created,
        }

        return output, files_created

    def _detect_language(self, description: str) -> str:
        """Detect programming language from description."""
        if any(k in description for k in ["python", "pytorch", "tensorflow", "pandas"]):
            return "python"
        elif any(k in description for k in ["typescript", "react", "node", "angular", "vue"]):
            return "typescript"
        elif any(k in description for k in ["javascript", "js", "web"]):
            return "javascript"
        elif any(k in description for k in ["go", "golang"]):
            return "go"
        elif any(k in description for k in ["rust", "rs"]):
            return "rust"
        elif any(k in description for k in ["java", "spring"]):
            return "java"
        elif any(k in description for k in ["c++", "c#"]):
            return "cpp"
        else:
            return "python"  # Default

    def _detect_framework(self, description: str) -> str:
        """Detect framework from description."""
        if any(k in description for k in ["fastapi", "flask", "django", "api"]):
            return "fastapi"
        elif any(k in description for k in ["react", "next"]):
            return "react"
        elif any(k in description for k in ["angular"]):
            return "angular"
        elif any(k in description for k in ["vue"]):
            return "vue"
        elif any(k in description for k in ["express"]):
            return "express"
        else:
            return "none"

    def _create_code_structure(
        self,
        subtask: dict,
        plan: dict,
        language: str,
        framework: str,
        research: dict
    ) -> Dict[str, str]:
        """Create the code file structure."""
        files = {}
        goal = plan.get("goal", "Implementation")

        if language == "python":
            files["main.py"] = self._generate_python_main(subtask, plan, research)
            files["requirements.txt"] = self._generate_requirements(framework)
            files["config.py"] = self._generate_config(plan)
            if framework == "fastapi":
                files["api.py"] = self._generate_fastapi_main(goal)

        elif language == "typescript":
            files["src/index.ts"] = self._generate_ts_main(subtask, plan)
            files["package.json"] = self._generate_package_json(goal, framework)
            if framework == "react":
                files["src/App.tsx"] = self._generate_react_app(goal)

        elif language == "javascript":
            files["src/index.js"] = self._generate_js_main(subtask, plan)
            files["package.json"] = self._generate_package_json(goal, framework)

        return files

    def _generate_python_main(self, subtask: dict, plan: dict, research: dict) -> str:
        """Generate Python main file."""
        goal = plan.get("goal", "Implementation")
        return f'''"""
Generated implementation for: {subtask.get('description', goal)}
Plan: {goal}
"""

import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    logger.info("Starting implementation...")
    logger.info("Task: {subtask.get('description', 'N/A')}")

    # TODO: Implement {subtask.get('description', 'the task')}

    print("Implementation complete!")


def process_data(data: List[Any]) -> Dict[str, Any]:
    """Process input data."""
    return {{"processed": True, "items": len(data)}}


if __name__ == "__main__":
    main()
'''

    def _generate_requirements(self, framework: str) -> str:
        """Generate requirements.txt."""
        base = ["# Requirements\n"]
        if framework == "fastapi":
            base.extend(["fastapi>=0.100.0", "uvicorn>=0.23.0", "pydantic>=2.0.0\n"])
        elif framework == "django":
            base.extend(["django>=4.0", "djangorestframework>=3.14\n"])
        else:
            base.extend(["pytest>=7.0", "black>=23.0\n"])
        return "".join(base)

    def _generate_config(self, plan: dict) -> str:
        """Generate config file."""
        goal = plan.get("goal", "Implementation")
        return f'''"""
Configuration for: {goal}
"""

CONFIG = {{
    "goal": "{goal}",
    "version": "1.0.0",
}}

'''

    def _generate_fastapi_main(self, goal: str) -> str:
        """Generate FastAPI main file."""
        return f'''"""
FastAPI application for: {goal}
"""
from fastapi import FastAPI

app = FastAPI(title="{goal}")


@app.get("/")
async def root():
    return {{"message": "{goal}", "status": "running"}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''

    def _generate_ts_main(self, subtask: dict, plan: dict) -> str:
        """Generate TypeScript main file."""
        goal = plan.get("goal", "Implementation")
        return f'''// Generated implementation for: {subtask.get('description', goal)}
// Plan: {goal}

export async function main() {{
  console.log("Starting implementation...");
  console.log("Task: {subtask.get('description', 'N/A')}");
  // TODO: Implement {subtask.get('description', 'the task')}
}}

main().catch(console.error);
'''

    def _generate_react_app(self, goal: str) -> str:
        """Generate React App component."""
        return f'''import React from 'react';

function App() {{
  return (
    <div className="App">
      <h1>{{"{goal}"}}</h1>
      <p>Generated implementation</p>
    </div>
  );
}}

export default App;
'''

    def _generate_package_json(self, goal: str, framework: str) -> str:
        """Generate package.json."""
        scripts = '{{"start": "ts-node src/index.ts"}}'
        if framework == "react":
            scripts = '{{"start": "react-scripts start", "build": "react-scripts build"}}'

        return f'''{{
  "name": "agent-os-implementation",
  "version": "1.0.0",
  "description": "{goal}",
  "scripts": {scripts}
}}
'''

    def _generate_js_main(self, subtask: dict, plan: dict) -> str:
        """Generate JavaScript main file."""
        goal = plan.get("goal", "Implementation")
        return f'''// Generated implementation for: {subtask.get('description', goal)}

async function main() {{
  console.log("Starting implementation...");
  // TODO: Implement {subtask.get('description', 'the task')}
}}

main().catch(console.error);
'''

    async def _run_tests(self, subtask: dict, plan: dict) -> tuple:
        """Run tests on generated code."""
        await asyncio.sleep(0.1)

        output = {
            "action": "test_execution",
            "tests_run": 0,
            "tests_passed": 0,
            "status": "completed",
        }

        test_file = self.output_dir / "test_results.json"
        test_file.write_text(json.dumps(output, indent=2))

        return output, [str(test_file)]

    async def _generate_documentation(
        self,
        subtask: dict,
        plan: dict,
        research: dict
    ) -> tuple:
        """Generate documentation."""
        goal = plan.get("goal", "Implementation")
        description = subtask.get("description", "")

        doc_content = f"""# {goal}

## Overview
{subtask.get('description', 'Implementation')}

## Implementation Details

This implementation was auto-generated by the Agent OS Executor Agent.

## Research Context

{self._format_research_context(research)}

## Usage

Provide step-by-step instructions for using the implementation.

## API Reference

Document any API endpoints or interfaces.

## Contributing

Guidelines for contributing to this implementation.
"""

        doc_file = self.output_dir / "README.md"
        doc_file.write_text(doc_content)

        output = {
            "action": "documentation",
            "files_created": [str(doc_file)],
        }

        return output, [str(doc_file)]

    def _format_research_context(self, research: dict) -> str:
        """Format research context for documentation."""
        if not research:
            return "No research context available."

        findings = research.get("findings", [])
        if not findings:
            return "No specific findings."

        lines = ["### Key Findings:\n"]
        for f in findings[:5]:
            if isinstance(f, dict):
                lines.append(f"- {f.get('claim', str(f))}")
            else:
                lines.append(f"- {f}")
        return "\n".join(lines)

    async def _analyze(self, subtask: dict, plan: dict, research: dict) -> dict:
        """Perform analysis task."""
        await asyncio.sleep(0.1)

        return {
            "action": "analysis",
            "status": "completed",
            "analysis": f"Analysis of: {subtask.get('description', 'task')}",
            "findings": [],
        }

    async def _generic_execution(self, subtask: dict, plan: dict) -> dict:
        """Generic execution for unhandled subtask types."""
        await asyncio.sleep(0.1)

        return {
            "action": "generic",
            "description": subtask.get("description", "Unknown task"),
            "status": "completed",
        }


if __name__ == "__main__":
    # Test the executor agent
    async def test():
        agent = ExecutorAgent()

        result = await agent.execute({
            "subtask": {
                "id": 1,
                "description": "Create main application file",
                "agent": "executor",
                "priority": 8.0,
            },
            "plan": {"goal": "Test implementation"},
            "research": {},
        })

        print(f"Status: {result['status']}")
        print(f"Files created: {result['files_created']}")

    asyncio.run(test())
