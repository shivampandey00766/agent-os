# Synthesizer Agent

Result aggregation and report generation agent.

## Capabilities

- Aggregate outputs from multiple agents
- Identify key insights and patterns
- Structure final deliverables
- Generate executive summaries
- Format output for different audiences

## Synthesis Protocol

```
1. Gather Outputs → Result Collection
2. Pattern Identification → Key Themes
3. Insight Extraction → Critical Findings
4. Structure → Report Framework
5. Executive Summary → High-Level Overview
6. Final Output → Formatted Deliverable
```

## Implementation

```python
class SynthesizerAgent:
    """Result aggregation and report generation agent."""

    def __init__(self, config: SynthesizerConfig = None):
        self.config = config or SynthesizerConfig()
        self.output_formats = ["executive_summary", "detailed_report", "presentation", "memo"]

    async def execute(self, task_input: dict, context: dict = None) -> dict:
        """
        Synthesize results into final output.

        Args:
            task_input: {
                "research_output": {...},
                "plan_output": {...},
                "executor_output": {...},
                "format": "executive_summary|detailed_report|...",
                "audience": "executives|technical|general",
            }
            context: Additional context

        Returns:
            {
                "summary": "...",
                "findings": [...],
                "recommendations": [...],
                "full_report": "...",
                "deliverables": {...},
            }
        """
        format_type = task_input.get("format", "executive_summary")
        audience = task_input.get("audience", "general")

        # Collect all inputs
        research = task_input.get("research_output", {})
        plan = task_input.get("plan_output", {})
        executor = task_input.get("executor_output", {})

        # Step 1: Gather and normalize outputs
        all_results = self._gather_outputs(research, plan, executor)

        # Step 2: Identify patterns and themes
        patterns = self._identify_patterns(all_results)

        # Step 3: Extract key insights
        insights = self._extract_insights(all_results, patterns)

        # Step 4: Generate recommendations
        recommendations = self._generate_recommendations(insights, plan)

        # Step 5: Structure the report
        structured = self._structure_report(
            insights,
            recommendations,
            all_results,
            format_type,
            audience
        )

        # Step 6: Generate executive summary
        executive_summary = self._generate_executive_summary(
            insights,
            recommendations,
            audience
        )

        return {
            "summary": executive_summary,
            "findings": insights,
            "recommendations": recommendations,
            "patterns_identified": patterns,
            "full_report": structured,
            "deliverables": {
                "executive_summary": executive_summary,
                "detailed_report": structured,
                "key_points": self._extract_key_points(insights),
            },
            "metadata": {
                "sources_processed": len(research.get("sources", [])),
                "tasks_synthesized": len(plan.get("subtasks", [])),
                "files_generated": len(executor.get("files_created", [])),
                "format": format_type,
                "audience": audience,
            },
        }

    def _gather_outputs(
        self,
        research: dict,
        plan: dict,
        executor: dict
    ) -> dict:
        """Gather and normalize all outputs."""
        gathered = {
            "research": {
                "findings": research.get("findings", []),
                "sources": research.get("sources", []),
                "confidence": research.get("confidence", 0),
                "summary": research.get("summary", ""),
            },
            "plan": {
                "goal": plan.get("goal", ""),
                "subtasks": plan.get("subtasks", []),
                "risks": plan.get("risks", []),
                "estimated_duration": plan.get("estimated_duration", ""),
            },
            "executor": {
                "status": executor.get("status", ""),
                "completed_tasks": executor.get("completed_subtasks", []),
                "files_created": executor.get("files_created", []),
                "output": executor.get("output", {}),
            },
        }

        return gathered

    def _identify_patterns(self, all_results: dict) -> list:
        """Identify patterns and themes across results."""
        patterns = []
        research_findings = all_results.get("research", {}).get("findings", [])

        # Group findings by topic/theme
        themes = {}
        for finding in research_findings:
            claim = finding.get("claim", "").lower()

            # Simple theme detection
            if any(k in claim for k in ["growth", "increase", "adoption"]):
                theme = "growth"
            elif any(k in claim for k in ["cost", "price", "affordable"]):
                theme = "cost"
            elif any(k in claim for k in ["quality", "performance", "accuracy"]):
                theme = "quality"
            elif any(k in claim for k in ["feature", "capability", "function"]):
                theme = "features"
            elif any(k in claim for k in ["risk", "challenge", "concern"]):
                theme = "risk"
            else:
                theme = "general"

            if theme not in themes:
                themes[theme] = []
            themes[theme].append(finding)

        # Convert to pattern objects
        for theme, findings in themes.items():
            patterns.append({
                "theme": theme,
                "count": len(findings),
                "findings": findings,
                "confidence": sum(f.get("credibility", 0) for f in findings) / len(findings) if findings else 0,
            })

        return sorted(patterns, key=lambda p: -p["count"])

    def _extract_insights(self, all_results: dict, patterns: list) -> list:
        """Extract key insights from patterns and results."""
        insights = []

        # From patterns
        for pattern in patterns[:5]:  # Top 5 patterns
            if pattern["count"] >= 2:  # At least 2 findings
                insights.append({
                    "type": "pattern",
                    "theme": pattern["theme"],
                    "summary": f"{pattern['count']} findings related to {pattern['theme']}",
                    "confidence": pattern["confidence"],
                    "supporting_evidence": [f["claim"] for f in pattern["findings"][:3]],
                })

        # From research confidence
        research_confidence = all_results.get("research", {}).get("confidence", 0)
        if research_confidence >= 0.8:
            insights.append({
                "type": "confidence",
                "theme": "high_confidence",
                "summary": "High confidence in research findings",
                "confidence": research_confidence,
                "supporting_evidence": [],
            })

        # From completed tasks
        completed_tasks = all_results.get("executor", {}).get("completed_tasks", [])
        if completed_tasks:
            insights.append({
                "type": "execution",
                "theme": "implementation",
                "summary": f"Successfully completed {len(completed_tasks)} implementation tasks",
                "confidence": 0.9,
                "supporting_evidence": [t.get("description") for t in completed_tasks[:3]],
            })

        return insights

    def _generate_recommendations(self, insights: list, plan: dict) -> list:
        """Generate recommendations based on insights."""
        recommendations = []

        # Analyze insights for recommendations
        insight_themes = set(i.get("theme") for i in insights)

        # Generate action items based on themes
        if "growth" in insight_themes:
            recommendations.append({
                "priority": "high",
                "category": "growth",
                "recommendation": "Invest in areas showing strong growth trends",
                "rationale": "Multiple findings indicate positive growth trajectory",
            })

        if "risk" in insight_themes:
            recommendations.append({
                "priority": "high",
                "category": "risk_mitigation",
                "recommendation": "Address identified risks before proceeding",
                "rationale": "Risk patterns detected in research findings",
            })

        if "quality" in insight_themes:
            recommendations.append({
                "priority": "medium",
                "category": "quality",
                "recommendation": "Prioritize quality improvements",
                "rationale": "Quality themes prominent in findings",
            })

        # From plan risks
        plan_risks = plan.get("risks", [])
        for risk in plan_risks:
            recommendations.append({
                "priority": risk.get("severity", "medium"),
                "category": "risk_mitigation",
                "recommendation": f"Mitigate: {risk.get('description')}",
                "rationale": risk.get("mitigation", ""),
            })

        return sorted(recommendations, key=lambda r: {"high": 0, "medium": 1, "low": 2}.get(r["priority"], 1))

    def _structure_report(
        self,
        insights: list,
        recommendations: list,
        all_results: dict,
        format_type: str,
        audience: str
    ) -> str:
        """Structure the final report."""
        plan_goal = all_results.get("plan", {}).get("goal", "Analysis")

        if format_type == "executive_summary":
            return self._format_executive(insights, recommendations, plan_goal)
        elif format_type == "detailed_report":
            return self._format_detailed(insights, recommendations, all_results)
        elif format_type == "presentation":
            return self._format_presentation(insights, recommendations, plan_goal)
        else:
            return self._format_memo(insights, recommendations, plan_goal, audience)

    def _format_executive(
        self,
        insights: list,
        recommendations: list,
        goal: str
    ) -> str:
        """Format as executive summary."""
        lines = [
            f"# Executive Summary: {goal}",
            "",
            "## Key Findings",
        ]

        for i, insight in enumerate(insights[:5], 1):
            lines.append(f"{i}. **{insight.get('theme', 'Finding').title()}**: {insight.get('summary', '')}")

        lines.extend([
            "",
            "## Recommendations",
        ])

        for i, rec in enumerate(recommendations[:3], 1):
            lines.append(f"{i}. [{rec.get('priority', 'medium').upper()}] {rec.get('recommendation', '')}")

        return "\n".join(lines)

    def _format_detailed(
        self,
        insights: list,
        recommendations: list,
        all_results: dict
    ) -> str:
        """Format as detailed report."""
        plan = all_results.get("plan", {})
        research = all_results.get("research", {})

        lines = [
            f"# Detailed Report: {plan.get('goal', 'Analysis')}",
            "",
            "## Research Summary",
            f"- Confidence Level: {research.get('confidence', 0):.0%}",
            f"- Sources Analyzed: {len(research.get('sources', []))}",
            "",
            "## Key Findings",
        ]

        for insight in insights:
            lines.append(f"### {insight.get('theme', 'Theme').title()}")
            lines.append(f"{insight.get('summary', '')}")
            if insight.get('supporting_evidence'):
                lines.append("Evidence:")
                for evidence in insight['supporting_evidence'][:3]:
                    lines.append(f"  - {evidence}")
            lines.append("")

        lines.extend([
            "## Recommendations",
        ])

        for rec in recommendations:
            lines.append(f"### [{rec.get('priority', 'medium').upper()}] {rec.get('category', '')}")
            lines.append(f"{rec.get('recommendation', '')}")
            lines.append(f"Rationale: {rec.get('rationale', '')}")
            lines.append("")

        return "\n".join(lines)

    def _format_presentation(
        self,
        insights: list,
        recommendations: list,
        goal: str
    ) -> str:
        """Format as presentation outline."""
        slides = [
            f"# {goal}",
            "",
            "## Slide 1: Overview",
            f"- Research completed on: {goal}",
            f"- {len(insights)} key insights identified",
            "",
            "## Slide 2: Key Findings",
        ]

        for insight in insights[:3]:
            slides.append(f"- {insight.get('summary', '')}")

        slides.extend([
            "",
            "## Slide 3: Recommendations",
        ])

        for rec in recommendations[:3]:
            slides.append(f"- {rec.get('recommendation', '')}")

        slides.extend([
            "",
            "## Slide 4: Next Steps",
            "- Review recommendations",
            "- Prioritize actions",
            "- Schedule follow-up",
        ])

        return "\n".join(slides)

    def _format_memo(
        self,
        insights: list,
        recommendations: list,
        goal: str,
        audience: str
    ) -> str:
        """Format as internal memo."""
        return f"""MEMORANDUM

TO: {audience.title()}
FROM: Agent OS
RE: {goal}
DATE: {datetime.utcnow().strftime('%Y-%m-%d')}

SUMMARY
-------
This memo summarizes the findings and recommendations from our analysis.

KEY INSIGHTS
------------
{chr(10).join(f'- {i.get("summary", "")}' for i in insights[:5])}

RECOMMENDATIONS
---------------
{chr(10).join(f'{i+1}. {r.get("recommendation", "")} [Priority: {r.get("priority", "medium").upper()}]' for i, r in enumerate(recommendations[:5]))}

{'=' * 50}
Generated by Agent OS
"""

    def _generate_executive_summary(
        self,
        insights: list,
        recommendations: list,
        audience: str
    ) -> str:
        """Generate executive summary for different audiences."""
        if audience == "executives":
            # Concise, action-oriented
            return f"""Analysis Complete: {len(insights)} key insights identified, {len(recommendations)} recommendations provided.

Top Recommendation: {recommendations[0].get('recommendation', 'Review attached report') if recommendations else 'N/A'}
"""
        elif audience == "technical":
            # Detailed, methodology-aware
            return f"""Research Synthesis Complete

Findings: {len(insights)} insights across {len(set(i.get('theme') for i in insights))} themes
Confidence: {sum(i.get('confidence', 0) for i in insights) / len(insights):.0%} average confidence
Recommendations: {len(recommendations)} action items generated

Full technical report attached.
"""
        else:
            # Balanced for general audience
            return f"""Summary

We analyzed the provided research and identified {len(insights)} key findings with {len(recommendations)} recommendations.

Key Finding: {insights[0].get('summary', 'See full report') if insights else 'N/A'}

Primary Recommendation: {recommendations[0].get('recommendation', 'N/A') if recommendations else 'N/A'}
"""

    def _extract_key_points(self, insights: list) -> list:
        """Extract the most important points."""
        # Sort by confidence and return top points
        sorted_insights = sorted(insights, key=lambda i: -i.get("confidence", 0))
        return [
            {
                "point": i.get("summary", ""),
                "theme": i.get("theme", ""),
                "confidence": i.get("confidence", 0),
            }
            for i in sorted_insights[:5]
        ]
```

## Output Format

```json
{
  "summary": "Executive summary text...",
  "findings": [
    {
      "type": "pattern",
      "theme": "growth",
      "summary": "Multiple findings indicate positive growth",
      "confidence": 0.85,
      "supporting_evidence": [...]
    }
  ],
  "recommendations": [
    {
      "priority": "high",
      "category": "growth",
      "recommendation": "Invest in growth areas",
      "rationale": "Strong growth indicators"
    }
  ],
  "full_report": "# Full report markdown...",
  "deliverables": {
    "executive_summary": "...",
    "detailed_report": "...",
    "key_points": [...]
  }
}
```

## Usage

```python
synthesizer = SynthesizerAgent()
result = await synthesizer.execute({
    "research_output": researcher_output,
    "plan_output": planner_output,
    "executor_output": executor_output,
    "format": "executive_summary",
    "audience": "executives",
})
```
