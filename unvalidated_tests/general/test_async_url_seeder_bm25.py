"""
Comprehensive test cases for AsyncUrlSeeder with BM25 scoring functionality.
Tests cover all features including query-based scoring, metadata extraction, 
edge cases, and integration scenarios.
"""

import pytest

import asyncio
from datetime import datetime

import httpx

from crawl4ai import AsyncLogger, AsyncUrlSeeder, SeedingConfig
from crawl4ai.async_url_seeder import COLLINFO_URL
from tests.helpers import TestCacheClient

# Test domain - using docs.crawl4ai.com as it has the actual documentation
TEST_DOMAIN = "kidocode.com"
TEST_DOMAIN = "docs.crawl4ai.com"
TEST_DOMAIN = "www.bbc.com/sport"

COMMON_CRAWL_INDEX_DATA = [
  {
    "id": "CC-MAIN-2025-47",
    "name": "November 2025 Index",
    "timegate": "https://index.commoncrawl.org/CC-MAIN-2025-47/",
    "cdx-api": "https://index.commoncrawl.org/CC-MAIN-2025-47-index",
    "from": "2025-11-06T20:07:18",
    "to": "2025-11-19T12:34:13"
  },
  {
    "id": "CC-MAIN-2025-43",
    "name": "October 2025 Index",
    "timegate": "https://index.commoncrawl.org/CC-MAIN-2025-43/",
    "cdx-api": "https://index.commoncrawl.org/CC-MAIN-2025-43-index",
    "from": "2025-10-05T11:42:39",
    "to": "2025-10-19T01:06:58"
  },
  {
    "id": "CC-MAIN-2025-38",
    "name": "September 2025 Index",
    "timegate": "https://index.commoncrawl.org/CC-MAIN-2025-38/",
    "cdx-api": "https://index.commoncrawl.org/CC-MAIN-2025-38-index",
    "from": "2025-09-05T11:21:01",
    "to": "2025-09-18T11:00:14"
  },
]

@pytest.fixture(autouse=True)
def mock_get_common_crawl_index(monkeypatch):
    original_get = httpx.AsyncClient.get
    
    async def mock_get(self, url, **kwargs):
        if url == COLLINFO_URL:
            return httpx.Response(status_code=200, request=httpx.Request(
                method="GET",
                url=url
            ), json=COMMON_CRAWL_INDEX_DATA)
        return await original_get(self, url, **kwargs)
    
    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)


class TestAsyncUrlSeederBM25:
    """Comprehensive test suite for AsyncUrlSeeder with BM25 scoring."""
    
    def create_seeder(self):
        """Create an AsyncUrlSeeder instance for testing."""
        logger = AsyncLogger()
        return AsyncUrlSeeder(cache_client=TestCacheClient(), logger=logger)
    
    # ============================================
    # Basic BM25 Scoring Tests
    # ============================================
    
    @pytest.mark.asyncio
    async def test_basic_bm25_scoring(self):
        seeder = self.create_seeder()

        """Test basic BM25 scoring with a simple query."""
        config = SeedingConfig(
            source="sitemap",
            extract_head=True,
            query="premier league highlights",
            scoring_method="bm25",
            max_urls=200,
            verbose=True,
            force=True  # Force fresh fetch
        )
        
        results = await seeder.urls(TEST_DOMAIN, config)
        
        # Verify results have relevance scores
        results_with_relevance_score = [r for r in results if "relevance_score" in r]
        assert results_with_relevance_score
        
        # Verify scores are normalized between 0 and 1
        scores = [r["relevance_score"] for r in results_with_relevance_score]
        assert all(0.0 <= s <= 1.0 for s in scores)
        
        # Verify results are sorted by relevance (descending)
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_query_variations(self):
        """Test BM25 scoring with different query variations."""
        seeder = self.create_seeder()
        queries = [
            "VAR controversy",
            "player ratings",
            "live score update",
            "transfer rumours",
            "post match analysis",
            "injury news"
        ]
        
        for query in queries:
            config = SeedingConfig(
                source="sitemap",
                extract_head=True,
                query=query,
                scoring_method="bm25",
                max_urls=100,
                # force=True 
            )
            
            results = await seeder.urls(TEST_DOMAIN, config)
            
            # Verify each query produces scored results
            results_with_relevance_score = [r for r in results if "relevance_score" in r]
            assert results_with_relevance_score
    
    # ============================================
    # Score Threshold Tests
    # ============================================
    
    @pytest.mark.asyncio
    async def test_score_threshold_filtering(self):
        """Test filtering results by minimum relevance score."""
        seeder = self.create_seeder()
        thresholds = [0.1, 0.3, 0.5, 0.7]
        
        for threshold in thresholds:
            config = SeedingConfig(
                source="sitemap",
                extract_head=True,
                query="league standings",
                score_threshold=threshold,
                scoring_method="bm25",
                max_urls=50
            )
            
            results = await seeder.urls(TEST_DOMAIN, config)
            
            # Verify all results meet threshold
            if results:
                assert all(r["relevance_score"] >= threshold for r in results)
    
    @pytest.mark.asyncio
    async def test_extreme_thresholds(self):
        """Test edge cases with extreme threshold values."""
        seeder = self.create_seeder()

        # Very low threshold - should return many results
        config_low = SeedingConfig(
            source="sitemap",
            extract_head=True,
            query="match",
            score_threshold=0.001,
            scoring_method="bm25"
        )
        results_low = await seeder.urls(TEST_DOMAIN, config_low)
        
        # Very high threshold - might return few or no results
        config_high = SeedingConfig(
            source="sitemap",
            extract_head=True,
            query="match",
            score_threshold=0.99,
            scoring_method="bm25"
        )
        results_high = await seeder.urls(TEST_DOMAIN, config_high)
        
        # Low threshold should return more results than high
        assert len(results_low) >= len(results_high)
    
    # ============================================
    # Metadata Extraction Tests
    # ============================================
    
    @pytest.mark.asyncio
    async def test_comprehensive_metadata_extraction(self):
        """Test extraction of all metadata types including JSON-LD."""
        seeder = self.create_seeder()
        config = SeedingConfig(
            source="sitemap",
            extract_head=True,
            query="match report",
            scoring_method="bm25",
            max_urls=5,
            verbose=True
        )
        
        results = await seeder.urls(TEST_DOMAIN, config)
        
        for result in results:
            head_data = result.get("head_data", {})
            
            # Check for various metadata fields
            print(f"\nMetadata for {result['url']}:")
            print(f"  Title: {head_data.get('title', 'N/A')}")
            print(f"  Charset: {head_data.get('charset', 'N/A')}")
            print(f"  Lang: {head_data.get('lang', 'N/A')}")
            
            # Check meta tags
            meta = head_data.get("meta", {})
            if meta:
                print("  Meta tags found:")
                for key in ["description", "keywords", "author", "viewport"]:
                    if key in meta:
                        print(f"    {key}: {meta[key][:50]}...")
            
            # Check for Open Graph tags
            og_tags = {k: v for k, v in meta.items() if k.startswith("og:")}
            if og_tags:
                print("  Open Graph tags found:")
                for k, v in list(og_tags.items())[:3]:
                    print(f"    {k}: {v[:50]}...")
            
            # Check JSON-LD
            if head_data.get("jsonld"):
                print(f"  JSON-LD schemas found: {len(head_data['jsonld'])}")
    
    @pytest.mark.asyncio
    async def test_jsonld_extraction_scoring(self):
        """Test that JSON-LD data contributes to BM25 scoring."""
        seeder = self.create_seeder()
        config = SeedingConfig(
            source="sitemap",
            extract_head=True,
            query="Premier League match report highlights",
            scoring_method="bm25",
            max_urls=20
        )
        
        results = await seeder.urls(TEST_DOMAIN, config)
        
        # Find results with JSON-LD data
        jsonld_results = [r for r in results if r.get("head_data", {}).get("jsonld")]
        
        if jsonld_results:
            print(f"\nFound {len(jsonld_results)} URLs with JSON-LD data")
            for r in jsonld_results[:3]:
                print(f"  Score: {r['relevance_score']:.3f} - {r['url']}")
                jsonld_data = r["head_data"]["jsonld"]
                print(f"    JSON-LD types: {[item.get('@type', 'Unknown') for item in jsonld_data if isinstance(item, dict)]}")
    
    # ============================================
    # Edge Cases and Error Handling
    # ============================================
    
    @pytest.mark.asyncio
    async def test_empty_query(self):
        """Test behavior with empty query string."""
        seeder = self.create_seeder()
        config = SeedingConfig(
            source="sitemap",
            extract_head=True,
            query="",
            scoring_method="bm25",
            max_urls=10
        )
        
        results = await seeder.urls(TEST_DOMAIN, config)
        
        # Should return results but all with zero scores
        assert len(results) > 0
        assert all(r.get("relevance_score", 0) == 0 for r in results)
    
    @pytest.mark.asyncio
    async def test_query_without_extract_head(self):
        """Test query scoring when extract_head is False."""
        seeder = self.create_seeder()
        config = SeedingConfig(
            source="sitemap",
            extract_head=False,  # This should trigger a warning
            query="Premier League match report highlights",
            scoring_method="bm25",
            max_urls=10
        )
        
        results = await seeder.urls(TEST_DOMAIN, config)
        
        # Results should not have relevance scores
        assert all("relevance_score" not in r for r in results)
        print("\nVerified: No scores added when extract_head=False")
    
    @pytest.mark.asyncio
    async def test_special_characters_in_query(self):
        """Test queries with special characters and symbols."""
        seeder = self.create_seeder()
        special_queries = [
            "premier league + analytics",
            "injury/rehab routines",
            "AI-powered scouting",
            "match stats & xG",
            "tactical@breakdown",
            "transfer-window.yml"
        ]
        
        for query in special_queries:
            config = SeedingConfig(
                source="sitemap",
                extract_head=True,
                query=query,
                scoring_method="bm25",
                max_urls=5
            )
            
            try:
                results = await seeder.urls(TEST_DOMAIN, config)
                assert isinstance(results, list)
                print(f"\n✓ Query '{query}' processed successfully")
            except Exception as e:
                pytest.fail(f"Failed on query '{query}': {str(e)}")
    
    @pytest.mark.asyncio
    async def test_unicode_query(self):
        """Test queries with Unicode characters."""
        seeder = self.create_seeder()
        unicode_queries = [
            "网页爬虫",  # Chinese
            "веб-краулер",  # Russian
            "🚀 crawl4ai",  # Emoji
            "naïve implementation",  # Accented characters
        ]
        
        for query in unicode_queries:
            config = SeedingConfig(
                source="sitemap",
                extract_head=True,
                query=query,
                scoring_method="bm25",
                max_urls=5
            )
            
            try:
                results = await seeder.urls(TEST_DOMAIN, config)
                assert isinstance(results, list)
                print(f"\n✓ Unicode query '{query}' processed successfully")
            except Exception as e:
                print(f"\n✗ Unicode query '{query}' failed: {str(e)}")
    
    # ============================================
    # Performance and Scalability Tests
    # ============================================
    
    @pytest.mark.asyncio
    async def test_large_scale_scoring(self):
        """Test BM25 scoring with many URLs."""
        seeder = self.create_seeder()
        config = SeedingConfig(
            source="cc+sitemap",  # Use both sources for more URLs
            extract_head=True,
            query="world cup group standings",
            scoring_method="bm25",
            max_urls=100,
            concurrency=20,
            hits_per_sec=10
        )
        
        start_time = asyncio.get_event_loop().time()
        results = await seeder.urls(TEST_DOMAIN, config)
        elapsed = asyncio.get_event_loop().time() - start_time
        
        print(f"\nProcessed {len(results)} URLs in {elapsed:.2f} seconds")
        print(f"Average time per URL: {elapsed/len(results)*1000:.1f}ms")
        
        # Verify scoring worked at scale
        results_with_relevance_score = [r for r in results if "relevance_score" in r]
        assert results_with_relevance_score
        
        # Check score distribution
        scores = [r["relevance_score"] for r in results_with_relevance_score]
        print("Score distribution:")
        print(f"  Min: {min(scores):.3f}")
        print(f"  Max: {max(scores):.3f}")
        print(f"  Avg: {sum(scores)/len(scores):.3f}")
    
    @pytest.mark.asyncio
    async def test_concurrent_scoring_consistency(self):
        """Test that concurrent requests produce consistent scores."""
        seeder = self.create_seeder()
        config = SeedingConfig(
            source="sitemap",
            extract_head=True,
            query="live score update",
            scoring_method="bm25",
            max_urls=20,
            concurrency=10
        )
        
        # Run the same query multiple times
        results_list = []
        for _ in range(3):
            results = await seeder.urls(TEST_DOMAIN, config)
            results_list.append(results)
        
        # Compare scores across runs (they should be identical for same URLs)
        url_scores = {}
        for results in results_list:
            for r in results:
                url = r["url"]
                score = r["relevance_score"]
                if url in url_scores:
                    # Scores should be very close
                    assert abs(url_scores[url] - score) < 0.01
                else:
                    url_scores[url] = score
        
        print(f"\n✓ Consistent scores across {len(results_list)} runs")
    
    # ============================================
    # Multi-Domain Tests
    # ============================================
    
    @pytest.mark.asyncio
    async def test_many_urls_with_scoring(self):
        """Test many_urls method with BM25 scoring."""
        seeder = self.create_seeder()
        domains = [TEST_DOMAIN, "docs.crawl4ai.com", "example.com"]
        
        config = SeedingConfig(
            source="sitemap",
            extract_head=True,
            # live_check=True,
            query="fixture list",
            scoring_method="bm25",
            score_threshold=0.2,
            max_urls=10,
            force=True,  # Force fresh fetch
        )
        
        results_dict = await seeder.many_urls(domains, config)
        
        for domain, results in results_dict.items():
            print(f"\nDomain: {domain}")
            print(f"  Found {len(results)} URLs above threshold")
            if results:
                top = results[0]
                print(f"  Top result: {top['relevance_score']:.3f} - {top['url']}")
    
    # ============================================
    # Complex Query Tests
    # ============================================
    
    @pytest.mark.asyncio
    async def test_multi_word_complex_queries(self):
        """Test complex multi-word queries."""
        seeder = self.create_seeder()
        complex_queries = [
            "how to follow live match commentary",
            "extract expected goals stats from match data",
            "premier league match report analysis",
            "transfer rumours and confirmed signings tracker",
            "tactical breakdown of high press strategy"
        ]
        
        for query in complex_queries:
            config = SeedingConfig(
                source="sitemap",
                extract_head=True,
                query=query,
                scoring_method="bm25",
                max_urls=5
            )
            
            results = await seeder.urls(TEST_DOMAIN, config)
            
            if results:
                print(f"\nQuery: '{query}'")
                print(f"Top match: {results[0]['relevance_score']:.3f} - {results[0]['url']}")
                
                # Extract matched terms from metadata
                head_data = results[0].get("head_data", {})
                title = head_data.get("title", "")
                description = head_data.get("meta", {}).get("description", "")
                
                # Simple term matching for verification
                query_terms = set(query.lower().split())
                title_terms = set(title.lower().split())
                desc_terms = set(description.lower().split())
                
                matched_terms = query_terms & (title_terms | desc_terms)
                if matched_terms:
                    print(f"Matched terms: {', '.join(matched_terms)}")
    
    # ============================================
    # Cache and Force Tests
    # ============================================
    
    @pytest.mark.asyncio
    async def test_scoring_with_cache(self):
        """Test that scoring works correctly with cached results."""
        seeder = self.create_seeder()
        config = SeedingConfig(
            source="sitemap",
            extract_head=True,
            query="injury update timeline",
            scoring_method="bm25",
            max_urls=10,
            force=False  # Use cache
        )
        
        # First run - populate cache
        results1 = await seeder.urls(TEST_DOMAIN, config)
        cache_count = seeder.cache_client.count()
        
        # Second run - should use cache
        results2 = await seeder.urls(TEST_DOMAIN, config)
        assert seeder.cache_client.count() == cache_count
        
        # Results should be identical
        assert len(results1) == len(results2)
        
        def sort_results(results):
            return sorted(results, key=lambda r: r["url"])
        
        for r1, r2 in zip(sort_results(results1), sort_results(results2)):
            assert r1["url"] == r2["url"]
            assert abs(r1["relevance_score"] - r2["relevance_score"]) < 0.001
        
        print("\n✓ Cache produces consistent scores")
    
    @pytest.mark.asyncio
    async def test_force_refresh_scoring(self):
        """Test force=True bypasses cache for fresh scoring."""
        seeder = self.create_seeder()
        config_cached = SeedingConfig(
            source="sitemap",
            extract_head=True,
            query="transfer window",
            scoring_method="bm25",
            max_urls=5,
            force=False
        )
        
        config_forced = SeedingConfig(
            source="sitemap",
            extract_head=True,
            query="transfer window",
            scoring_method="bm25",
            max_urls=5,
            force=True
        )
        
        # Run with cache
        start1 = asyncio.get_event_loop().time()
        results1 = await seeder.urls(TEST_DOMAIN, config_cached)
        time1 = asyncio.get_event_loop().time() - start1
        
        # Run with force (should be slower due to fresh fetch)
        start2 = asyncio.get_event_loop().time()
        results2 = await seeder.urls(TEST_DOMAIN, config_forced)
        time2 = asyncio.get_event_loop().time() - start2
        
        print(f"\nCached run: {time1:.2f}s")
        print(f"Forced run: {time2:.2f}s")
        
        # Both should produce scored results
        assert all("relevance_score" in r for r in results1)
        assert all("relevance_score" in r for r in results2)
    
    # ============================================
    # Source Combination Tests
    # ============================================
    
    @pytest.mark.asyncio
    async def test_scoring_with_multiple_sources(self):
        """Test BM25 scoring with combined sources (cc+sitemap)."""
        seeder = self.create_seeder()
        config = SeedingConfig(
            source="cc+sitemap",
            extract_head=True,
            query="match highlights video",
            scoring_method="bm25",
            score_threshold=0.3,
            max_urls=30,
            concurrency=15
        )
        
        results = await seeder.urls(TEST_DOMAIN, config)
        
        # Verify we got results from both sources
        print(f"\nCombined sources returned {len(results)} URLs above threshold")
        
        # Check URL diversity
        unique_paths = set()
        for r in results:
            path = r["url"].replace("https://", "").replace("http://", "").split("/", 1)[-1]
            unique_paths.add(path.split("?")[0])  # Remove query params
        
        print(f"Unique paths found: {len(unique_paths)}")
        
        # All should be scored and above threshold
        assert all(r["relevance_score"] >= 0.3 for r in results)
    
    # ============================================
    # Integration Tests
    # ============================================
    
    @pytest.mark.asyncio
    async def test_full_workflow_integration(self):
        """Test complete workflow: discover -> score -> filter -> use."""
        seeder = self.create_seeder()
        # Step 1: Discover and score URLs
        config = SeedingConfig(
            source="sitemap",
            extract_head=True,
            query="premier league opening fixtures",
            scoring_method="bm25",
            score_threshold=0.4,
            max_urls=10,
            verbose=True
        )
        
        results = await seeder.urls(TEST_DOMAIN, config)
        
        print(f"\nStep 1: Found {len(results)} relevant URLs")
        
        # Step 2: Analyze top results
        if results:
            top_urls = results[:3]
            print("\nStep 2: Top 3 URLs for crawling:")
            for i, r in enumerate(top_urls):
                print(f"{i+1}. Score: {r['relevance_score']:.3f}")
                print(f"   URL: {r['url']}")
                print(f"   Title: {r['head_data'].get('title', 'N/A')}")
                
                # Check metadata quality
                meta = r['head_data'].get('meta', {})
                if 'description' in meta:
                    print(f"   Description: {meta['description'][:80]}...")
        
        # Step 3: Verify these URLs would be good for actual crawling
        assert all(r["status"] == "valid" for r in results[:3])
        print("\nStep 3: All top URLs are valid for crawling ✓")
    
    # ============================================
    # Report Generation
    # ============================================
    
    @pytest.mark.asyncio
    async def test_generate_scoring_report(self):
        """Generate a comprehensive report of BM25 scoring effectiveness."""
        seeder = self.create_seeder()
        queries = {
            "beginner": "match schedule",
            "advanced": "tactical analysis pressing",
            "api": "VAR decision explanation",
            "deployment": "fixture changes due to weather",
            "extraction": "expected goals statistics"
        }
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "domain": TEST_DOMAIN,
            "results": {}
        }
        
        for category, query in queries.items():
            config = SeedingConfig(
                source="sitemap",
                extract_head=True,
                query=query,
                scoring_method="bm25",
                max_urls=10
            )
            
            results = await seeder.urls(TEST_DOMAIN, config)
            
            report["results"][category] = {
                "query": query,
                "total_results": len(results),
                "top_results": [
                    {
                        "url": r["url"],
                        "score": r["relevance_score"],
                        "title": r["head_data"].get("title", "")
                    }
                    for r in results[:3]
                ],
                "score_distribution": {
                    "min": min(r["relevance_score"] for r in results) if results else 0,
                    "max": max(r["relevance_score"] for r in results) if results else 0,
                    "avg": sum(r["relevance_score"] for r in results) / len(results) if results else 0
                }
            }
        
        # Print report
        print("\n" + "="*60)
        print("BM25 SCORING EFFECTIVENESS REPORT")
        print("="*60)
        print(f"Domain: {report['domain']}")
        print(f"Timestamp: {report['timestamp']}")
        print("\nResults by Category:")
        
        for category, data in report["results"].items():
            print(f"\n{category.upper()}: '{data['query']}'")
            print(f"  Total results: {data['total_results']}")
            print(f"  Score range: {data['score_distribution']['min']:.3f} - {data['score_distribution']['max']:.3f}")
            print(f"  Average score: {data['score_distribution']['avg']:.3f}")
            print("  Top matches:")
            for i, result in enumerate(data['top_results']):
                print(f"    {i+1}. [{result['score']:.3f}] {result['title']}")

