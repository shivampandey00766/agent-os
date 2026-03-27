"""
Synthesizer Agent - Result aggregation and report generation.
Aggregates outputs from multiple agents into final deliverables.
"""

import asyncio
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Finding:
    """A key insight or finding."""
    type: str  # pattern, confidence, execution
    theme: str
    summary: str
    confidence: float
    supporting_evidence: List[str]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Recommendation:
    """An action recommendation."""
    priority: str  # high, medium, low
    category: str
    recommendation: str
    rationale: str

    def to_dict(self) -> dict:
        return asdict(self)


class SynthesizerAgent:
    """
    Result aggregation and report generation agent.

    Synthesis Protocol:
    1. Gather Outputs → Result Collection
    2. Pattern Identification → Key Themes
    3. Insight Extraction → Critical Findings
    4. Structure → Report Framework
    5. Executive Summary → High-Level Overview
    6. Final Output → Formatted Deliverable
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
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
            "findings": [f.to_dict() if isinstance(f, Finding) else f for f in insights],
            "recommendations": [r.to_dict() if isinstance(r, Recommendation) else r for r in recommendations],
            "patterns_identified": patterns,
            "full_report": structured,
            "deliverables": {
                "executive_summary": executive_summary,
                "detailed_report": structured,
                "key_points": self._extract_key_points(insights),
            },
            "metadata": {
                "sources_processed": len(research.get("sources", [])) if isinstance(research, dict) else 0,
                "tasks_synthesized": len(plan.get("subtasks", [])) if isinstance(plan, dict) else 0,
                "files_generated": len(executor.get("files_created", [])) if isinstance(executor, dict) else 0,
                "format": format_type,
                "audience": audience,
                "generated_at": datetime.utcnow().isoformat(),
            },
        }

    def _gather_outputs(self, research: dict, plan: dict, executor: dict) -> dict:
        """Gather and normalize all outputs."""
        gathered = {
            "research": {
                "findings": research.get("findings", []) if isinstance(research, dict) else [],
                "sources": research.get("sources", []) if isinstance(research, dict) else [],
                "confidence": research.get("confidence", 0) if isinstance(research, dict) else 0,
                "summary": research.get("summary", "") if isinstance(research, dict) else "",
            },
            "plan": {
                "goal": plan.get("goal", "") if isinstance(plan, dict) else "",
                "subtasks": plan.get("subtasks", []) if isinstance(plan, dict) else [],
                "risks": plan.get("risks", []) if isinstance(plan, dict) else [],
                "estimated_duration": plan.get("estimated_duration", "") if isinstance(plan, dict) else "",
            },
            "executor": {
                "status": executor.get("status", "") if isinstance(executor, dict) else "",
                "completed_tasks": executor.get("results", []) if isinstance(executor, dict) else [],
                "files_created": executor.get("files_created", []) if isinstance(executor, dict) else [],
                "output": executor,
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
            if isinstance(finding, dict):
                claim = finding.get("claim", "").lower()
            else:
                claim = str(finding).lower()

            # Simple theme detection
            if any(k in claim for k in ["growth", "increase", "adoption", "expansion"]):
                theme = "growth"
            elif any(k in claim for k in ["cost", "price", "affordable", "expensive", "cheap"]):
                theme = "cost"
            elif any(k in claim for k in ["quality", "performance", "accuracy", "speed"]):
                theme = "quality"
            elif any(k in claim for k in ["feature", "capability", "function", "integration"]):
                theme = "features"
            elif any(k in claim for k in ["risk", "challenge", "concern", "threat", "issue"]):
                theme = "risk"
            elif any(k in claim for k in ["market", "share", "competition", "competitor"]):
                theme = "market"
            elif any(k in claim for k in ["enterprise", "business", "company", "organization"]):
                theme = "enterprise"
            else:
                theme = "general"

            if theme not in themes:
                themes[theme] = []
            themes[theme].append(finding)

        # Convert to pattern objects
        for theme, findings in themes.items():
            if isinstance(findings[0], dict):
                avg_credibility = sum(f.get("credibility", 0) for f in findings) / len(findings) if findings else 0
            else:
                avg_credibility = 0.5

            patterns.append({
                "theme": theme,
                "count": len(findings),
                "findings": findings,
                "confidence": avg_credibility,
            })

        return sorted(patterns, key=lambda p: -p["count"])

    def _extract_insights(self, all_results: dict, patterns: list) -> list:
        """Extract key insights from patterns and results."""
        insights = []

        # From patterns
        for pattern in patterns[:5]:  # Top 5 patterns
            if pattern["count"] >= 1:  # At least 1 finding
                insights.append(Finding(
                    type="pattern",
                    theme=pattern["theme"],
                    summary=f"{pattern['count']} findings related to {pattern['theme']}",
                    confidence=pattern["confidence"],
                    supporting_evidence=self._extract_evidence(pattern["findings"][:3]),
                ))

        # From research confidence
        research_confidence = all_results.get("research", {}).get("confidence", 0)
        if research_confidence >= 0.8:
            insights.append(Finding(
                type="confidence",
                theme="high_confidence",
                summary="High confidence in research findings",
                confidence=research_confidence,
                supporting_evidence=[],
            ))

        # From completed tasks
        completed_tasks = all_results.get("executor", {}).get("completed_tasks", [])
        if completed_tasks:
            task_count = len(completed_tasks) if isinstance(completed_tasks, list) else 0
            insights.append(Finding(
                type="execution",
                theme="implementation",
                summary=f"Successfully completed {task_count} implementation tasks",
                confidence=0.9,
                supporting_evidence=[],
            ))

        return insights

    def _extract_evidence(self, findings: list) -> list:
        """Extract evidence strings from findings."""
        evidence = []
        for f in findings:
            if isinstance(f, dict):
                evidence.append(f.get("claim", str(f)))
            else:
                evidence.append(str(f))
        return evidence

    def _generate_recommendations(self, insights: list, plan: dict) -> list:
        """Generate recommendations based on insights."""
        recommendations = []

        # Analyze insights for recommendations
        insight_themes = set(i.theme for i in insights if isinstance(i, Finding))
        insight_themes.update(set(i.get("theme") for i in insights if isinstance(i, dict)))

        # Generate action items based on themes
        if "growth" in insight_themes:
            recommendations.append(Recommendation(
                priority="high",
                category="growth",
                recommendation="Invest in areas showing strong growth trends",
                rationale="Multiple findings indicate positive growth trajectory",
            ))

        if "risk" in insight_themes:
            recommendations.append(Recommendation(
                priority="high",
                category="risk_mitigation",
                recommendation="Address identified risks before proceeding",
                rationale="Risk patterns detected in research findings",
            ))

        if "quality" in insight_themes:
            recommendations.append(Recommendation(
                priority="medium",
                category="quality",
                recommendation="Prioritize quality improvements",
                rationale="Quality themes prominent in findings",
            ))

        if "cost" in insight_themes:
            recommendations.append(Recommendation(
                priority="medium",
                category="cost",
                recommendation="Review cost optimization opportunities",
                rationale="Cost-related findings detected",
            ))

        if "features" in insight_themes:
            recommendations.append(Recommendation(
                priority="medium",
                category="product",
                recommendation="Enhance feature set based on findings",
                rationale="Feature capabilities are a key theme",
            ))

        # From plan risks
        plan_risks = plan.get("risks", []) if isinstance(plan, dict) else []
        for risk in plan_risks:
            if isinstance(risk, dict):
                recommendations.append(Recommendation(
                    priority=risk.get("severity", "medium"),
                    category="risk_mitigation",
                    recommendation=f"Mitigate: {risk.get('description', 'identified risk')}",
                    rationale=risk.get("mitigation", ""),
                ))

        return sorted(recommendations, key=lambda r: {"high": 0, "medium": 1, "low": 2}.get(r.priority, 1))

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
        research = all_results.get("research", {})

        if format_type == "executive_summary":
            return self._format_executive(insights, recommendations, plan_goal)
        elif format_type == "detailed_report":
            return self._format_detailed(insights, recommendations, all_results)
        elif format_type == "presentation":
            return self._format_presentation(insights, recommendations, plan_goal)
        else:
            return self._format_memo(insights, recommendations, plan_goal, audience)

    def _format_executive(self, insights: list, recommendations: list, goal: str) -> str:
        """Format as executive summary."""
        lines = [
            f"# Executive Summary: {goal}",
            "",
            "## Key Findings",
        ]

        for i, insight in enumerate(insights[:5], 1):
            theme = insight.theme if isinstance(insight, Finding) else insight.get("theme", "Finding")
            summary = insight.summary if isinstance(insight, Finding) else insight.get("summary", "")
            lines.append(f"{i}. **{theme.title()}**: {summary}")

        lines.extend([
            "",
            "## Recommendations",
        ])

        for i, rec in enumerate(recommendations[:3], 1):
            priority = rec.priority if isinstance(rec, Recommendation) else rec.get("priority", "medium")
            rec_text = rec.recommendation if isinstance(rec, Recommendation) else rec.get("recommendation", "")
            lines.append(f"{i}. [{priority.upper()}] {rec_text}")

        return "\n".join(lines)

    def _format_detailed(self, insights: list, recommendations: list, all_results: dict) -> str:
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
            theme = insight.theme if isinstance(insight, Finding) else insight.get("theme", "Theme")
            summary = insight.summary if isinstance(insight, Finding) else insight.get("summary", "")
            lines.append(f"### {theme.title()}")
            lines.append(summary)

            evidence = insight.supporting_evidence if isinstance(insight, Finding) else insight.get("supporting_evidence", [])
            if evidence:
                lines.append("Evidence:")
                for ev in evidence[:3]:
                    lines.append(f"  - {ev}")
            lines.append("")

        lines.extend([
            "## Recommendations",
        ])

        for rec in recommendations:
            priority = rec.priority if isinstance(rec, Recommendation) else rec.get("priority", "medium")
            category = rec.category if isinstance(rec, Recommendation) else rec.get("category", "")
            rec_text = rec.recommendation if isinstance(rec, Recommendation) else rec.get("recommendation", "")
            rationale = rec.rationale if isinstance(rec, Recommendation) else rec.get("rationale", "")

            lines.append(f"### [{priority.upper()}] {category.title()}")
            lines.append(rec_text)
            lines.append(f"Rationale: {rationale}")
            lines.append("")

        return "\n".join(lines)

    def _format_presentation(self, insights: list, recommendations: list, goal: str) -> str:
        """Format as presentation outline."""
        slides = [
            f"# {goal}",
            "",
            "## Slide 1: Overview",
            f"- Analysis completed on: {goal}",
            f"- {len(insights)} key insights identified",
            "",
            "## Slide 2: Key Findings",
        ]

        for insight in insights[:3]:
            theme = insight.theme if isinstance(insight, Finding) else insight.get("theme", "")
            summary = insight.summary if isinstance(insight, Finding) else insight.get("summary", "")
            slides.append(f"- {theme.title()}: {summary}")

        slides.extend([
            "",
            "## Slide 3: Recommendations",
        ])

        for rec in recommendations[:3]:
            rec_text = rec.recommendation if isinstance(rec, Recommendation) else rec.get("recommendation", "")
            slides.append(f"- {rec_text}")

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
        lines = [
            "MEMORANDUM",
            "",
            f"TO: {audience.title()}",
            "FROM: Agent OS Synthesizer",
            f"RE: {goal}",
            f"DATE: {datetime.utcnow().strftime('%Y-%m-%d')}",
            "",
            "SUMMARY",
            "-" * 40,
        ]

        for insight in insights[:5]:
            summary = insight.summary if isinstance(insight, Finding) else insight.get("summary", "")
            lines.append(f"- {summary}")

        lines.extend([
            "",
            "RECOMMENDATIONS",
            "-" * 40,
        ])

        for i, rec in enumerate(recommendations[:5], 1):
            rec_text = rec.recommendation if isinstance(rec, Recommendation) else rec.get("recommendation", "")
            priority = rec.priority if isinstance(rec, Recommendation) else rec.get("priority", "medium")
            lines.append(f"{i}. {rec_text} [Priority: {priority.upper()}]")

        lines.extend([
            "",
            "=" * 40,
            "Generated by Agent OS",
        ])

        return "\n".join(lines)

    def _generate_executive_summary(
        self,
        insights: list,
        recommendations: list,
        audience: str
    ) -> str:
        """Generate executive summary for different audiences."""
        insight_count = len(insights)
        rec_count = len(recommendations)
        top_rec = recommendations[0] if recommendations else None
        top_rec_text = top_rec.recommendation if isinstance(top_rec, Recommendation) else (top_rec.get("recommendation", "N/A") if top_rec else "N/A")
        top_insight = insights[0] if insights else None
        top_insight_text = top_insight.summary if isinstance(top_insight, Finding) else (top_insight.get("summary", "N/A") if top_insight else "N/A")

        if audience == "executives":
            return f"""Analysis Complete: {insight_count} key insights identified, {rec_count} recommendations provided.

Top Recommendation: {top_rec_text}
"""
        elif audience == "technical":
            avg_confidence = sum(i.confidence if isinstance(i, Finding) else i.get("confidence", 0) for i in insights) / max(1, insight_count)
            return f"""Research Synthesis Complete

Findings: {insight_count} insights across {len(set(i.theme if isinstance(i, Finding) else i.get("theme", "") for i in insights))} themes
Confidence: {avg_confidence:.0%} average confidence
Recommendations: {rec_count} action items generated

Full technical report attached.
"""
        else:
            return f"""Summary

We analyzed the provided research and identified {insight_count} key findings with {rec_count} recommendations.

Key Finding: {top_insight_text}

Primary Recommendation: {top_rec_text}
"""

    def _extract_key_points(self, insights: list) -> list:
        """Extract the most important points."""
        # Sort by confidence and return top points
        sorted_insights = sorted(
            insights,
            key=lambda i: -(i.confidence if isinstance(i, Finding) else i.get("confidence", 0))
        )
        return [
            {
                "point": i.summary if isinstance(i, Finding) else i.get("summary", ""),
                "theme": i.theme if isinstance(i, Finding) else i.get("theme", ""),
                "confidence": i.confidence if isinstance(i, Finding) else i.get("confidence", 0),
            }
            for i in sorted_insights[:5]
        ]


if __name__ == "__main__":
    # Test the synthesizer agent
    async def test():
        agent = SynthesizerAgent()

        result = await agent.execute({
            "research_output": {
                "findings": [
                    {"claim": "AI market growing 25% annually", "credibility": 0.85},
                    {"claim": "Enterprise adoption increasing", "credibility": 0.90},
                ],
                "confidence": 0.87,
                "sources": ["source1.com", "source2.com"],
            },
            "plan_output": {
                "goal": "AI market analysis",
                "subtasks": [],
                "risks": [],
            },
            "executor_output": {
                "status": "completed",
                "files_created": ["file1.py"],
            },
            "format": "executive_summary",
            "audience": "executives",
        })

        print(f"Summary: {result['summary'][:100]}...")
        print(f"Findings: {len(result['findings'])}")
        print(f"Recommendations: {len(result['recommendations'])}")

    asyncio.run(test())
