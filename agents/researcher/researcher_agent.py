"""
Research Agent - Deep web research implementation.
Uses WebSearch, WebFetch, and BrowserMCP for comprehensive research.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ResearchFinding:
    """A single research finding."""
    claim: str
    source: str
    source_type: str  # academic, official, news, blog, forum
    credibility: float
    url: str
    key_points: List[str]
    retrieved_at: str = None

    def __post_init__(self):
        if self.retrieved_at is None:
            self.retrieved_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ResearchFinding":
        return cls(**data)


@dataclass
class SearchResult:
    """A search result from an engine."""
    url: str
    title: str
    snippet: str
    engine: str
    rank: int

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SearchResult":
        return cls(**data)


class ResearcherAgent:
    """
    Deep research agent using WebSearch, WebFetch, and BrowserMCP.

    Research Protocol:
    1. Query Analysis → Search Strategy
    2. Parallel Web Searches
    3. Deep Content Extraction
    4. Source Validation
    5. Finding Synthesis
    6. Confidence Scoring
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.search_engines = self.config.get("engines", ["web"])
        self.credibility_weights = {
            "academic": 1.0,
            "official": 0.9,
            "news": 0.7,
            "blog": 0.5,
            "forum": 0.3,
            "unknown": 0.2,
        }

    async def execute(self, task_input: dict, context: dict = None) -> dict:
        """
        Execute deep research on the given topic.

        Args:
            task_input: {
                "query": "research topic",
                "depth": "standard|comprehensive",
                "sources": ["web", "academic", "news"],
                "max_sources": 20,
            }
            context: Additional context from orchestrator

        Returns:
            {
                "findings": [...],
                "sources": [...],
                "confidence": 0.85,
                "summary": "...",
            }
        """
        query = task_input.get("query")
        depth = task_input.get("depth", "standard")
        max_sources = task_input.get("max_sources", 20)

        # Step 1: Analyze query and formulate search strategy
        search_strategy = self._analyze_query(query)

        # Step 2: Execute parallel searches
        search_results = await self._parallel_search(query, search_strategy)

        # Step 3: Extract deep content
        extracted_content = await self._extract_content(search_results[:max_sources])

        # Step 4: Validate sources
        validated = await self._validate_sources(extracted_content)

        # Step 5: Synthesize findings
        findings = self._synthesize_findings(validated)

        # Step 6: Calculate confidence
        confidence = self._calculate_confidence(findings, validated)

        return {
            "findings": [f.to_dict() if isinstance(f, ResearchFinding) else f for f in findings],
            "sources": [s["url"] for s in validated],
            "source_details": validated,
            "confidence": confidence,
            "summary": self._generate_summary(findings),
            "search_strategy": search_strategy,
            "query": query,
            "depth": depth,
        }

    def _analyze_query(self, query: str) -> dict:
        """Analyze query and create search strategy."""
        keywords = query.lower().split()
        intent_type = self._classify_intent(query)

        return {
            "primary_terms": keywords[:5],
            "secondary_terms": keywords[5:10] if len(keywords) > 5 else [],
            "intent": intent_type,
            "search_formulations": self._generate_search_formulations(query),
        }

    def _classify_intent(self, query: str) -> str:
        """Classify the research intent."""
        query_lower = query.lower()

        if any(k in query_lower for k in ["compare", "vs", "versus", "difference"]):
            return "comparison"
        elif any(k in query_lower for k in ["how", "what", "why", "when"]):
            return "explanatory"
        elif any(k in query_lower for k in ["latest", "new", "recent", "2026", "2025"]):
            return "trends"
        elif any(k in query_lower for k in ["best", "top", "recommend"]):
            return "recommendation"
        else:
            return "general"

    def _generate_search_formulations(self, query: str) -> list:
        """Generate multiple search query formulations."""
        return [
            query,
            f'"{query}"',
            f'{query} 2026',
            f'{query} comprehensive guide',
            f'{query} analysis',
        ]

    async def _parallel_search(self, query: str, strategy: dict) -> list:
        """Execute searches across multiple engines in parallel."""
        tasks = []

        for engine in self.search_engines:
            for formulation in strategy["search_formulations"][:2]:
                tasks.append(self._search_engine(engine, formulation))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten and deduplicate
        seen_urls = set()
        unique_results = []

        for result_list in results:
            if isinstance(result_list, Exception):
                continue
            for result in result_list:
                if isinstance(result, dict) and result.get("url") not in seen_urls:
                    seen_urls.add(result["url"])
                    unique_results.append(result)

        return unique_results

    async def _search_engine(self, engine: str, query: str) -> list:
        """Search a specific engine using WebSearch MCP."""
        # In production, this would use:
        # from mcp_tools import web_search
        # return await web_search(query, engine=engine)

        # For now, return placeholder
        return [
            {
                "url": f"https://example.com/search?q={query.replace(' ', '+')}",
                "title": f"Search result for {query}",
                "snippet": f"Results related to {query}...",
                "engine": engine,
                "rank": 1,
            }
        ]

    async def _extract_content(self, search_results: list) -> list:
        """Extract deep content from search results."""
        if not search_results:
            return []

        tasks = [self._fetch_content(r) for r in search_results]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return [r for r in results if not isinstance(r, Exception)]

    async def _fetch_content(self, result: dict) -> dict:
        """Fetch and extract content from a URL using WebFetch MCP."""
        # In production:
        # from mcp_tools import web_fetch
        # content = await web_fetch(result["url"])
        # return self._parse_content(result, content)

        return {
            **result,
            "content": result.get("snippet", ""),
            "word_count": len(result.get("snippet", "").split()),
            "key_points": self._extract_key_points(result.get("snippet", "")),
        }

    def _extract_key_points(self, text: str) -> list:
        """Extract key points from text."""
        if not text:
            return []

        sentences = text.split('.')
        return [s.strip() for s in sentences[:3] if s.strip()]

    async def _validate_sources(self, content: list) -> list:
        """Validate and score sources."""
        validated = []

        for item in content:
            if isinstance(item, Exception):
                continue

            credibility = self._score_source(item)
            source_type = self._classify_source_type(item.get("url", ""))

            if credibility >= 0.3:  # Minimum threshold
                validated.append({
                    **item,
                    "credibility_score": credibility,
                    "source_type": source_type,
                })

        return sorted(validated, key=lambda x: -x["credibility_score"])

    def _score_source(self, source: dict) -> float:
        """Calculate credibility score for a source."""
        url = source.get("url", "")

        # Type-based scoring
        source_type = self._classify_source_type(url)
        type_score = self.credibility_weights.get(source_type, 0.2)

        # Content-based adjustments
        word_count = source.get("word_count", 0)
        content_score = min(1.0, word_count / 1000)  # 1000 words = 1.0

        # Recency (simplified - would check actual dates in production)
        recency_score = 0.8

        # Weighted combination
        return (type_score * 0.5) + (content_score * 0.3) + (recency_score * 0.2)

    def _classify_source_type(self, url: str) -> str:
        """Classify the type of source based on URL."""
        url_lower = url.lower()

        if any(d in url_lower for d in [".edu", "arxiv.org", "scholar", "research", "pubmed"]):
            return "academic"
        elif any(d in url_lower for d in [".gov", "official", ".org"]):
            return "official"
        elif any(d in url_lower for d in ["news", "article", "press"]):
            return "news"
        elif any(d in url_lower for d in ["blog", "medium", "substack"]):
            return "blog"
        elif any(d in url_lower for d in ["reddit", "forum", "stack", "discord"]):
            return "forum"
        else:
            return "unknown"

    def _synthesize_findings(self, validated_sources: list) -> list:
        """Synthesize findings from validated sources."""
        findings = []
        seen_claims = set()

        for source in validated_sources:
            key_points = source.get("key_points", [])
            for point in key_points:
                if not point:
                    continue
                # Deduplicate similar claims
                point_hash = hash(point.lower().strip())
                if point_hash not in seen_claims:
                    seen_claims.add(point_hash)
                    findings.append(ResearchFinding(
                        claim=point,
                        source=source.get("url", ""),
                        source_type=source.get("source_type", "unknown"),
                        credibility=source.get("credibility_score", 0.5),
                        url=source.get("url", ""),
                        key_points=[point],
                    ))

        return findings

    def _calculate_confidence(self, findings: list, sources: list) -> float:
        """Calculate overall confidence in the research."""
        if not findings:
            return 0.0

        # Average credibility of sources
        avg_credibility = sum(s.get("credibility_score", 0) for s in sources) / len(sources) if sources else 0

        # Coverage score (how many aspects of query were covered)
        coverage = min(1.0, len(findings) / 20)

        # Source diversity bonus
        unique_domains = len(set(self._extract_domain(s.get("url", "")) for s in sources))
        diversity = min(1.0, unique_domains / 10)

        # Weighted combination
        confidence = (avg_credibility * 0.4) + (coverage * 0.3) + (diversity * 0.3)

        return round(confidence, 2)

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return ""

    def _generate_summary(self, findings: list) -> str:
        """Generate a summary of findings."""
        if not findings:
            return "No significant findings."

        top_findings = findings[:5]
        summary = "Key findings:\n"

        for i, finding in enumerate(top_findings, 1):
            summary += f"{i}. {finding.claim} (confidence: {finding.credibility:.0%})\n"

        return summary


if __name__ == "__main__":
    # Test the researcher agent
    async def test():
        agent = ResearcherAgent()

        result = await agent.execute({
            "query": "AI coding assistants competitive landscape 2026",
            "depth": "comprehensive",
        })

        print(f"Confidence: {result['confidence']}")
        print(f"Findings: {len(result['findings'])}")
        print(f"Summary: {result['summary']}")

    asyncio.run(test())
