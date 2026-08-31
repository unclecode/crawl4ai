"""
Test script for debugging confidence calculation in adaptive crawler
Focus: Testing why confidence decreases when crawling relevant URLs
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict
import math

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from crawl4ai import AsyncWebCrawler
from crawl4ai.adaptive_crawler import CrawlState, StatisticalStrategy
from crawl4ai.models import CrawlResult


class ConfidenceTestHarness:
    """Test harness for analyzing confidence calculation"""
    
    def __init__(self):
        self.strategy = StatisticalStrategy()
        self.test_urls = [
            'https://docs.python.org/3/library/asyncio.html',
            'https://docs.python.org/3/library/asyncio-runner.html', 
            'https://docs.python.org/3/library/asyncio-api-index.html',
            'https://docs.python.org/3/library/contextvars.html',
            'https://docs.python.org/3/library/asyncio-stream.html'
        ]
        self.query = "async await context manager"
        
    async def test_confidence_progression(self):
        """Test confidence calculation as we crawl each URL"""
        print(f"Testing confidence for query: '{self.query}'")
        print("=" * 80)
        
        # Initialize state
        state = CrawlState(query=self.query)
        
        # Create crawler
        async with AsyncWebCrawler() as crawler:
            for i, url in enumerate(self.test_urls, 1):
                print(f"\n{i}. Crawling: {url}")
                print("-" * 80)
                
                # Crawl the URL
                result = await crawler.arun(url=url)
                
                # Extract markdown content
                if hasattr(result, '_results') and result._results:
                    result = result._results[0]
                
                # Create a mock CrawlResult with markdown
                mock_result = type('CrawlResult', (), {
                    'markdown': type('Markdown', (), {
                        'raw_markdown': result.markdown.raw_markdown if hasattr(result, 'markdown') else ''
                    })(),
                    'url': url
                })()
                
                # Update state
                state.knowledge_base.append(mock_result)
                await self.strategy.update_state(state, [mock_result])
                
                # Calculate metrics
                confidence = await self.strategy.calculate_confidence(state)
                
                # Get individual components
                coverage = state.metrics.get('coverage', 0)
                consistency = state.metrics.get('consistency', 0)
                saturation = state.metrics.get('saturation', 0)
                
                # Analyze term frequencies
                query_terms = self.strategy._tokenize(self.query.lower())
                term_stats = {}
                for term in query_terms:
                    term_stats[term] = {
                        'tf': state.term_frequencies.get(term, 0),
                        'df': state.document_frequencies.get(term, 0)
                    }
                
                # Print detailed results
                print(f"State after crawl {i}:")
                print(f"  Total documents: {state.total_documents}")
                print(f"  Unique terms: {len(state.term_frequencies)}")
                print(f"  New terms added: {state.new_terms_history[-1] if state.new_terms_history else 0}")
                
                print(f"\nQuery term statistics:")
                for term, stats in term_stats.items():
                    print(f"  '{term}': tf={stats['tf']}, df={stats['df']}")
                
                print(f"\nMetrics:")
                print(f"  Coverage: {coverage:.3f}")
                print(f"  Consistency: {consistency:.3f}")
                print(f"  Saturation: {saturation:.3f}")
                print(f"  → Confidence: {confidence:.3f}")
                
                # Show coverage calculation details
                print(f"\nCoverage calculation details:")
                self._debug_coverage_calculation(state, query_terms)
                
                # Alert if confidence decreased
                if i > 1 and confidence < state.metrics.get('prev_confidence', 0):
                    print(f"\n⚠️  WARNING: Confidence decreased from {state.metrics.get('prev_confidence', 0):.3f} to {confidence:.3f}")
                
                state.metrics['prev_confidence'] = confidence
    
    def _debug_coverage_calculation(self, state: CrawlState, query_terms: List[str]):
        """Debug coverage calculation step by step"""
        coverage_score = 0.0
        max_possible_score = 0.0
        
        for term in query_terms:
            tf = state.term_frequencies.get(term, 0)
            df = state.document_frequencies.get(term, 0)
            
            if df > 0:
                idf = math.log((state.total_documents - df + 0.5) / (df + 0.5) + 1)
                doc_coverage = df / state.total_documents
                tf_boost = min(tf / df, 3.0)
                term_score = doc_coverage * idf * (1 + 0.1 * math.log1p(tf_boost))
                
                print(f"    '{term}': doc_cov={doc_coverage:.2f}, idf={idf:.2f}, boost={1 + 0.1 * math.log1p(tf_boost):.2f} → score={term_score:.3f}")
                coverage_score += term_score
            else:
                print(f"    '{term}': not found → score=0.000")
            
            max_possible_score += 1.0 * 1.0 * 1.1
        
        print(f"    Total: {coverage_score:.3f} / {max_possible_score:.3f} = {coverage_score/max_possible_score if max_possible_score > 0 else 0:.3f}")
        
        # New coverage calculation
        print(f"\n  NEW Coverage calculation (without IDF):")
        new_coverage = self._calculate_coverage_new(state, query_terms)
        print(f"    → New Coverage: {new_coverage:.3f}")
    
    def _calculate_coverage_new(self, state: CrawlState, query_terms: List[str]) -> float:
        """New coverage calculation without IDF"""
        if not query_terms or state.total_documents == 0:
            return 0.0
            
        term_scores = []
        max_tf = max(state.term_frequencies.values()) if state.term_frequencies else 1
        
        for term in query_terms:
            tf = state.term_frequencies.get(term, 0)
            df = state.document_frequencies.get(term, 0)
            
            if df > 0:
                # Document coverage: what fraction of docs contain this term
                doc_coverage = df / state.total_documents
                
                # Frequency signal: normalized log frequency
                freq_signal = math.log(1 + tf) / math.log(1 + max_tf) if max_tf > 0 else 0
                
                # Combined score: document coverage with frequency boost
                term_score = doc_coverage * (1 + 0.5 * freq_signal)
                
                print(f"    '{term}': doc_cov={doc_coverage:.2f}, freq_signal={freq_signal:.2f} → score={term_score:.3f}")
                term_scores.append(term_score)
            else:
                print(f"    '{term}': not found → score=0.000")
                term_scores.append(0.0)
        
        # Average across all query terms
        coverage = sum(term_scores) / len(term_scores)
        return coverage


async def main():
    """Run the confidence test"""
    tester = ConfidenceTestHarness()
    await tester.test_confidence_progression()
    
    print("\n" + "=" * 80)
    print("Test complete!")


if __name__ == "__main__":
    asyncio.run(main())