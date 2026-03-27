# Researcher Agent

Deep web research agent using WebSearch, WebFetch, and BrowserMCP.

## Capabilities

- Parallel web searches across multiple engines
- Deep content extraction from web pages
- Source credibility scoring
- Finding deduplication
- Confidence scoring

## Research Protocol

```
1. Query Analysis → Search Strategy
2. Parallel Web Searches
3. Deep Content Extraction
4. Source Validation
5. Finding Synthesis
6. Confidence Scoring
```

## Implementation

```python
class ResearcherAgent:
    """Deep research agent for comprehensive topic investigation."""

    def __init__(self, config: ResearcherConfig = None):
        self.config = config or ResearcherConfig()
        self.search_engines = ["perplexity", "firecrawl", "tavily"]
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
                "sources": ["web", "academic", "news"],  # optional
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

        # Step 1: Analyze query and formulate search strategy
        search_strategy = self._analyze_query(query)

        # Step 2: Execute parallel searches
        search_results = await self._parallel_search(query, search_strategy)

        # Step 3: Extract deep content
        extracted_content = await self._extract_content(search_results)

        # Step 4: Validate sources
        validated = await self._validate_sources(extracted_content)

        # Step 5: Synthesize findings
        findings = self._synthesize_findings(validated)

        # Step 6: Calculate confidence
        confidence = self._calculate_confidence(findings, validated)

        return {
            "findings": findings,
            "sources": [s["url"] for s in validated],
            "source_details": validated,
            "confidence": confidence,
            "summary": self._generate_summary(findings),
            "search_strategy": search_strategy,
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
                if result["url"] not in seen_urls:
                    seen_urls.add(result["url"])
                    unique_results.append(result)

        return unique_results

    async def _search_engine(self, engine: str, query: str) -> list:
        """Search a specific engine."""
        # Placeholder - actual implementation would use MCP tools
        return [
            {
                "url": f"https://example.com/{engine}/{hash(query)}",
                "title": f"Result for {query}",
                "snippet": "...",
                "engine": engine,
                "rank": 1,
            }
        ]

    async def _extract_content(self, search_results: list) -> list:
        """Extract deep content from search results."""
        tasks = [self._fetch_content(r) for r in search_results[:10]]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _fetch_content(self, result: dict) -> dict:
        """Fetch and extract content from a URL."""
        # Placeholder - actual implementation would use WebFetch/BrowserMCP
        return {
            **result,
            "content": "Extracted content...",
            "word_count": 500,
            "key_points": ["point 1", "point 2"],
        }

    async def _validate_sources(self, content: list) -> list:
        """Validate and score sources."""
        validated = []

        for item in content:
            if isinstance(item, Exception):
                continue

            credibility = self._score_source(item)
            if credibility >= 0.3:  # Minimum threshold
                validated.append({
                    **item,
                    "credibility_score": credibility,
                    "credibility_type": self._classify_source_type(item["url"]),
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

        # Recency (simplified)
        recency_score = 0.8  # Default

        return (type_score * 0.5) + (content_score * 0.3) + (recency_score * 0.2)

    def _classify_source_type(self, url: str) -> str:
        """Classify the type of source based on URL."""
        url_lower = url.lower()

        if any(d in url_lower for d in [".edu", "arxiv.org", "scholar", "research"]):
            return "academic"
        elif any(d in url_lower for d in [".gov", "official", ".org"]):
            return "official"
        elif any(d in url_lower for d in ["news", "article", "press"]):
            return "news"
        elif any(d in url_lower for d in ["blog", "medium", "substack"]):
            return "blog"
        elif any(d in url_lower for d in ["reddit", "forum", "stack"]):
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
                # Deduplicate similar claims
                point_hash = hash(point.lower().strip())
                if point_hash not in seen_claims:
                    seen_claims.add(point_hash)
                    findings.append({
                        "claim": point,
                        "source": source["url"],
                        "credibility": source["credibility_score"],
                    })

        return findings

    def _calculate_confidence(self, findings: list, sources: list) -> float:
        """Calculate overall confidence in the research."""
        if not findings:
            return 0.0

        # Average credibility of sources
        avg_credibility = sum(s["credibility_score"] for s in sources) / len(sources) if sources else 0

        # Coverage score (how many aspects of query were covered)
        coverage = min(1.0, len(findings) / 20)

        # Source diversity bonus
        unique_domains = len(set(self._extract_domain(s["url"]) for s in sources))
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
            summary += f"{i}. {finding['claim']} (confidence: {finding['credibility']:.0%})\n"

        return summary
```

## Source Citation Format

```json
{
  "findings": [
    {
      "claim": "LLM adoption increased 300% in 2025",
      "source": "https://arxiv.org/example",
      "credibility": 0.95,
      "retrieved_at": "2026-03-27T10:00:00Z"
    }
  ]
}
```

## Usage

```python
researcher = ResearcherAgent()
result = await researcher.execute({
    "query": "AI coding assistant competitive landscape 2026",
    "depth": "comprehensive",
})
```
