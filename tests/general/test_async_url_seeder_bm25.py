"""
Comprehensive test cases for AsyncUrlSeeder with BM25 scoring functionality.
Tests cover all features including query-based scoring, metadata extraction, 
edge cases, and integration scenarios.
"""

import asyncio
import pytest
from typing import List, Dict, Any
from crawl4ai import AsyncUrlSeeder, SeedingConfig, AsyncLogger
import json
from datetime import datetime

# Test domain - using docs.crawl4ai.com as it has the actual documentation
TEST_DOMAIN = "kidocode.com"
TEST_DOMAIN = "docs.crawl4ai.com"
TEST_DOMAIN = "www.bbc.com/sport"


class TestAsyncUrlSeederBM25:
    """Comprehensive test suite for AsyncUrlSeeder with BM25 scoring."""
    
    async def create_seeder(self):
        """Create an AsyncUrlSeeder instance for testing."""
        logger = AsyncLogger()
        return AsyncUrlSeeder(logger=logger)

    # ============================================
    # Basic BM25 Scoring Tests
    # ============================================
    
    @pytest.mark.asyncio
    async def test_basic_bm25_scoring(self, seeder):
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
        assert all("relevance_score" in r for r in results)
        
        # Verify scores are normalized between 0 and 1
        scores = [r["relevance_score"] for r in results]
        assert all(0.0 <= s <= 1.0 for s in scores)
        
        # Verify results are sorted by relevance (descending)
        assert scores == sorted(scores, reverse=True)
        
        # Print top 5 results for manual verification
        print("\nTop 5 results for 'web crawling tutorial':")
        for i, r in enumerate(results[:5]):
            print(f"{i+1}. Score: {r['relevance_score']:.3f} - {r['url']}")
    
    @pytest.mark.asyncio
    async def test_query_variations(self, seeder):
        """Test BM25 scoring with different query variations."""
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
            assert len(results) > 0
            assert all("relevance_score" in r for r in results)
            
            print(f"\nTop result for '{query}':")
            if results:
                top = results[0]
                print(f"  Score: {top['relevance_score']:.3f} - {top['url']}")
    
    # ============================================
    # Score Threshold Tests
    # ============================================
    
    @pytest.mark.asyncio
    async def test_score_threshold_filtering(self, seeder):
        """Test filtering results by minimum relevance score."""
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
            
            print(f"\nThreshold {threshold}: {len(results)} URLs passed")
    
    @pytest.mark.asyncio
    async def test_extreme_thresholds(self, seeder):
        """Test edge cases with extreme threshold values."""
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
        print(f"\nLow threshold (0.001): {len(results_low)} results")
        print(f"High threshold (0.99): {len(results_high)} results")
    
    # ============================================
    # Metadata Extraction Tests
    # ============================================
    
    @pytest.mark.asyncio
    async def test_comprehensive_metadata_extraction(self, seeder):
        """Test extraction of all metadata types including JSON-LD."""
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
    async def test_jsonld_extraction_scoring(self, seeder):
        """Test that JSON-LD data contributes to BM25 scoring."""
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
    async def test_empty_query(self, seeder):
        """Test behavior with empty query string."""
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
    async def test_query_without_extract_head(self, seeder):
        """Test query scoring when extract_head is False."""
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
    async def test_special_characters_in_query(self, seeder):
        """Test queries with special characters and symbols."""
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
    async def test_unicode_query(self, seeder):
        """Test queries with Unicode characters."""
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
    async def test_large_scale_scoring(self, seeder):
        """Test BM25 scoring with many URLs."""
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
        assert all("relevance_score" in r for r in results)
        
        # Check score distribution
        scores = [r["relevance_score"] for r in results]
        print(f"Score distribution:")
        print(f"  Min: {min(scores):.3f}")
        print(f"  Max: {max(scores):.3f}")
        print(f"  Avg: {sum(scores)/len(scores):.3f}")
    
    @pytest.mark.asyncio
    async def test_concurrent_scoring_consistency(self, seeder):
        """Test that concurrent requests produce consistent scores."""
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
                    # Scores should be very close (allowing for tiny float differences)
                    assert abs(url_scores[url] - score) < 0.001
                else:
                    url_scores[url] = score
        
        print(f"\n✓ Consistent scores across {len(results_list)} runs")
    
    # ============================================
    # Multi-Domain Tests
    # ============================================
    
    @pytest.mark.asyncio
    async def test_many_urls_with_scoring(self, seeder):
        """Test many_urls method with BM25 scoring."""
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
    async def test_multi_word_complex_queries(self, seeder):
        """Test complex multi-word queries."""
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
    async def test_scoring_with_cache(self, seeder):
        """Test that scoring works correctly with cached results."""
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
        
        # Second run - should use cache
        results2 = await seeder.urls(TEST_DOMAIN, config)
        
        # Results should be identical
        assert len(results1) == len(results2)
        for r1, r2 in zip(results1, results2):
            assert r1["url"] == r2["url"]
            assert abs(r1["relevance_score"] - r2["relevance_score"]) < 0.001
        
        print("\n✓ Cache produces consistent scores")
    
    @pytest.mark.asyncio
    async def test_force_refresh_scoring(self, seeder):
        """Test force=True bypasses cache for fresh scoring."""
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
    async def test_scoring_with_multiple_sources(self, seeder):
        """Test BM25 scoring with combined sources (cc+sitemap)."""
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
    async def test_full_workflow_integration(self, seeder):
        """Test complete workflow: discover -> score -> filter -> use."""
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
    async def test_generate_scoring_report(self, seeder):
        """Generate a comprehensive report of BM25 scoring effectiveness."""
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


# ============================================
# Standalone test runner
# ============================================

async def run_all_tests():
    """Run all tests standalone (without pytest)."""
    print("Running AsyncUrlSeeder BM25 Tests...")
    print("="*60)
    
    test_instance = TestAsyncUrlSeederBM25()
    seeder = await test_instance.create_seeder()
    
    # Run each test method
    test_methods = [
        # test_instance.test_basic_bm25_scoring,
        # test_instance.test_query_variations,
        # test_instance.test_score_threshold_filtering,
        # test_instance.test_extreme_thresholds,
        # test_instance.test_comprehensive_metadata_extraction,
        # test_instance.test_jsonld_extraction_scoring,
        # test_instance.test_empty_query,
        # test_instance.test_query_without_extract_head,
        # test_instance.test_special_characters_in_query,
        # test_instance.test_unicode_query,
        # test_instance.test_large_scale_scoring,
        # test_instance.test_concurrent_scoring_consistency,
        # test_instance.test_many_urls_with_scoring,
        test_instance.test_multi_word_complex_queries,
        test_instance.test_scoring_with_cache,
        test_instance.test_force_refresh_scoring,
        test_instance.test_scoring_with_multiple_sources,
        test_instance.test_full_workflow_integration,
        test_instance.test_generate_scoring_report
    ]
    
    for test_method in test_methods:
        try:
            print(f"\nRunning {test_method.__name__}...")
            await test_method(seeder)
            print(f"✓ {test_method.__name__} passed")
        except Exception as e:
            import traceback
            print(f"✗ {test_method.__name__} failed: {str(e)}")
            print(f"  Error type: {type(e).__name__}")
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("Test suite completed!")


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(run_all_tests())