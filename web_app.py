"""
Agent OS Web Application
Flask web UI for the Agent OS deep research system.
"""

import asyncio
import sys
from flask import Flask, render_template, request, jsonify, redirect, url_for

sys.path.insert(0, "C:/Users/Shiva/Downloads/agent-os")

from kernel.orchestrator import Orchestrator
from kernel.task_queue import TaskQueue, TaskType
from kernel.memory import MemoryManager
from kernel.self_improver import SelfImprover

app = Flask(__name__)
app.config['SECRET_KEY'] = 'agent-os-secret-key-2026'


def get_kernel():
    """Get kernel component instances."""
    return {
        'queue': TaskQueue(),
        'memory': MemoryManager(),
        'improver': SelfImprover(),
    }


@app.route('/')
def dashboard():
    """Main dashboard with stats."""
    queue = TaskQueue()
    memory = MemoryManager()
    improver = SelfImprover()

    queue_stats = queue.get_queue_stats()
    memory_stats = memory.get_stats()
    dashboard_data = improver.get_dashboard()
    recommendations = improver.get_recommendations()

    pending_tasks = queue.get_pending_tasks()
    in_progress = queue.get_in_progress_tasks()

    # Get recent episodes
    episodes = memory.get_recent_episodes(limit=5)
    episode_list = []
    for ep in episodes:
        episode_list.append({
            'id': ep.id,
            'description': ep.description,
            'outcome': getattr(ep, 'outcome', 'unknown'),
            'tags': getattr(ep, 'tags', []),
        })

    return render_template(
        'dashboard.html',
        queue_stats=queue_stats,
        memory_stats=memory_stats,
        dashboard=dashboard_data,
        recommendations=recommendations,
        pending_tasks=pending_tasks[:10],
        in_progress=in_progress[:10],
        episodes=episode_list,
    )


@app.route('/research', methods=['GET', 'POST'])
def research():
    """Research form and submission."""
    queue = TaskQueue()

    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        depth = request.form.get('depth', 'standard')
        priority = int(request.form.get('priority', 5))

        if query:
            # Enqueue the research task
            task = queue.enqueue(
                task_type=TaskType.RESEARCH.value,
                input_data={'query': query, 'depth': depth},
                priority=priority
            )

            # Run the task immediately
            asyncio.run(run_research_async(task.id, query, depth))

            return redirect(url_for('results', task_id=task.id))

        return render_template('research.html', error="Query cannot be empty")

    # GET request - show form
    pending = queue.get_pending_tasks()
    recent = queue.get_completed_tasks()[:10]

    return render_template(
        'research.html',
        pending_tasks=pending,
        recent_tasks=recent
    )


def run_research_async(task_id: str, query: str, depth: str):
    """Run research task asynchronously."""
    orchestrator = Orchestrator()
    asyncio.run(orchestrator.run(initial_task={
        'type': 'research',
        'input': {'query': query, 'depth': depth},
        'priority': 10
    }))


@app.route('/results/<task_id>')
def results(task_id):
    """Show research results for a task."""
    queue = TaskQueue()
    task = queue.get_task(task_id)

    if not task:
        return render_template('results.html', error=f"Task {task_id} not found")

    output = task.output or {}
    findings = output.get('findings', [])
    sources = output.get('source_details', [])
    confidence = output.get('confidence', 0)
    summary = output.get('summary', '')
    query = output.get('query', task.input.get('query', 'Unknown') if task.input else 'Unknown')

    return render_template(
        'results.html',
        task_id=task_id,
        status=task.status,
        query=query,
        confidence=confidence,
        findings=findings,
        sources=sources,
        summary=summary,
        task=task,
    )


@app.route('/api/stats')
def stats_json():
    """JSON endpoint for stats (for AJAX updates)."""
    queue = TaskQueue()
    memory = MemoryManager()
    improver = SelfImprover()

    return jsonify({
        'queue': queue.get_queue_stats(),
        'memory': memory.get_stats(),
        'quality': improver.get_dashboard(),
    })


@app.route('/api/research', methods=['POST'])
def api_research():
    """API endpoint to start research task."""
    data = request.get_json()
    query = data.get('query', '').strip()
    depth = data.get('depth', 'standard')
    priority = int(data.get('priority', 5))

    if not query:
        return jsonify({'error': 'Query is required'}), 400

    queue = TaskQueue()
    task = queue.enqueue(
        task_type=TaskType.RESEARCH.value,
        input_data={'query': query, 'depth': depth},
        priority=priority
    )

    # Run asynchronously
    run_research_async(task.id, query, depth)

    return jsonify({
        'task_id': task.id,
        'status': 'started',
        'query': query,
    })


if __name__ == '__main__':
    print("=" * 60)
    print("Agent OS Web UI")
    print("Open http://localhost:5000 in your browser")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
