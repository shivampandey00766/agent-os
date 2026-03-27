---
name: web-researcher
category: research
description: Deep web research using WebSearch, WebFetch, and BrowserMCP for comprehensive topic investigation
version: 1.0.0
---

# Web Researcher Skill

Performs deep web research using multiple search engines and content extraction.

## Usage

```
/skill web-researcher --query "AI coding assistants 2026" --depth comprehensive
```

## Capabilities

- Parallel web searches across multiple engines
- Deep content extraction from web pages
- Source credibility scoring
- Finding deduplication
- Confidence scoring

## Research Protocol

```
1. Query Analysis → Search Strategy
2. Parallel Web Searches (Perplexity, Firecrawl, Tavily)
3. Deep Content Extraction
4. Source Validation
5. Finding Synthesis
6. Confidence Scoring
```

## Implementation

```python
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ResearchResult:
    """A single research finding."""
    claim: str
    source: str
    source_type: str  # academic, official, news, blog, forum
    credibility: float
    url: str
    retrieved_at: str = None

    def __post_init__(self):
        if self.retrieved_at is None:
            self.retrieved_at = datetime.utcnow().isoformat()


class WebResearcher:
    """Deep research using WebSearch, WebFetch, and BrowserMCP."""

    def __init__(self):
        self.search_engines = ["perplexity", "firecrawl", "tavily"]
        self.credibility_weights = {
            "academic": 1.0,
            "official": 0.9,
            "news": 0.7,
            "blog": 0.5,
            "forum": 0.3,
        }

    async def research(
        self,
        query: str,
        depth: str = "standard",
        max_sources: int = 20
    ) -> Dict[str, Any]:
        """
        Perform deep research on a topic.

        Args:
            query: Research query
            depth: "standard" or "comprehensive"
            max_sources: Maximum number of sources to analyze

        Returns:
            {
                "findings": [...],
                "sources": [...],
                "confidence": 0.85,
                "summary": "..."
            }
        """
        # Step 1: Analyze query
        strategy = self._analyze_query(query)

        # Step 2: Execute parallel searches
        search_results = await self._parallel_search(query, strategy)

        # Step 3: Extract content
        extracted = await self._extract_content(search_results[:max_sources])

        # Step 4: Validate sources
        validated = self._validate_sources(extracted)

        # Step 5: Synthesize
        findings = self._synthesize_findings(validated)

        # Step 6: Score confidence
        confidence = self._calculate_confidence(findings, validated)

        return {
            "findings": findings,
            "sources": [v["url"] for v in validated],
            "source_details": validated,
            "confidence": confidence,
            "summary": self._generate_summary(findings),
            "search_strategy": strategy,
        }

    def _analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query and create search strategy."""
        keywords = query.lower().split()
        intent = self._classify_intent(query)

        return {
            "primary_terms": keywords[:5],
            "secondary_terms": keywords[5:10] if len(keywords) > 5 else [],
            "intent": intent,
            "formulations": [
                query,
                f'"{query}"',
                f'{query} 2026',
                f'{query} comprehensive',
            ],
        }

    def _classify_intent(self, query: str) -> str:
        """Classify research intent."""
        q = query.lower()
        if any(k in q for k in ["compare", "vs", "versus"]):
            return "comparison"
        elif any(k in q for k in ["latest", "new", "recent"]):
            return "trends"
        elif any(k in q for k in ["best", "top", "recommend"]):
            return "recommendation"
        return "general"

    async def _parallel_search(self, query: str, strategy: Dict) -> List[Dict]:
        """Execute searches across multiple engines."""
        # Use MCP tools for actual search
        # This is a placeholder that would use:
        # - WebSearch (built-in)
        # - BrowserMCP for JavaScript-heavy pages
        # - Tavily/Perplexity APIs

        tasks = []
        for engine in self.search_engines:
            for formulation in strategy["formulations"][:2]:
                tasks.append(self._search_engine(engine, formulation))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Deduplicate
        seen = set()
        unique = []
        for r in results:
            if isinstance(r, Exception):
                continue
            for item in r:
                if item["url"] not in seen:
                    seen.add(item["url"])
                    unique.append(item)
        return unique

    async def _search_engine(self, engine: str, query: str) -> List[Dict]:
        """Search a specific engine. Implementation uses MCP."""
        # Placeholder - actual implementation via MCP tools
        return []

    async def _extract_content(self, urls: List[str]) -> List[Dict]:
        """Extract content from URLs using WebFetch/BrowserMCP."""
        tasks = [self._fetch_url(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _fetch_url(self, url: str) -> Dict:
        """Fetch and extract content from a URL."""
        # Uses WebFetch MCP tool
        return {
            "url": url,
            "title": "",
            "content": "",
            "word_count": 0,
            "key_points": [],
        }

    def _validate_sources(self, content: List[Dict]) -> List[Dict]:
        """Validate and score sources."""
        validated = []
        for item in content:
            if isinstance(item, Exception):
                continue
            score = self._score_source(item)
            if score >= 0.3:
                validated.append({
                    **item,
                    "credibility_score": score,
                    "source_type": self._classify_source_type(item["url"]),
                })
        return sorted(validated, key=lambda x: -x["credibility_score"])

    def _score_source(self, source: Dict) -> float:
        """Calculate credibility score."""
        source_type = self._classify_source_type(source.get("url", ""))
        type_score = self.credibility_weights.get(source_type, 0.2)
        word_count = source.get("word_count", 0)
        content_score = min(1.0, word_count / 1000)
        return (type_score * 0.6) + (content_score * 0.4)

    def _classify_source_type(self, url: str) -> str:
        """Classify source type by URL."""
        url_lower = url.lower()
        if any(d in url_lower for d in [".edu", "arxiv", "scholar"]):
            return "academic"
        elif any(d in url_lower for d in [".gov", "official", ".org"]):
            return "official"
        elif any(d in url_lower for d in ["news", "article", "press"]):
            return "news"
        elif any(d in url_lower for d in ["blog", "medium"]):
            return "blog"
        return "unknown"

    def _synthesize_findings(self, sources: List[Dict]) -> List[Dict]:
        """Synthesize findings from validated sources."""
        seen = set()
        findings = []
        for source in sources:
            for point in source.get("key_points", []):
                key = hash(point.lower().strip())
                if key not in seen:
                    seen.add(key)
                    findings.append({
                        "claim": point,
                        "source": source["url"],
                        "credibility": source["credibility_score"],
                    })
        return findings

    def _calculate_confidence(self, findings: List, sources: List) -> float:
        """Calculate overall confidence."""
        if not findings:
            return 0.0
        avg_cred = sum(s["credibility_score"] for s in sources) / len(sources)
        coverage = min(1.0, len(findings) / 20)
        diversity = min(1.0, len(set(self._extract_domain(s["url"]) for s in sources)) / 10)
        return round((avg_cred * 0.5) + (coverage * 0.3) + (diversity * 0.2), 2)

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        from urllib.parse import urlparse
        return urlparse(url).netloc

    def _generate_summary(self, findings: List) -> str:
        """Generate summary of findings."""
        if not findings:
            return "No significant findings."
        top = findings[:5]
        lines = ["Key findings:"]
        for i, f in enumerate(top, 1):
            lines.append(f"{i}. {f['claim']} (confidence: {f['credibility']:.0%})")
        return "\n".join(lines)
```

## Integration with Agent OS

```python
from agent_os.kernel.task_queue import TaskQueue, TaskType

async def run_research(query: str):
    researcher = WebResearcher()
    result = await researcher.research(query, depth="comprehensive")

    # Store in semantic memory
    memory = MemoryManager()
    memory.add_semantic(
        f"research_{uuid.uuid4()}",
        result,
        tags=["research", query.split()[:3]]
    )

    # Enqueue for planner
    queue = TaskQueue()
    queue.enqueue(TaskType.PLAN.value, {"goal": query, "research": result})

    return result
```
