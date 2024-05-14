import unittest, os
from crawl4ai.web_crawler import WebCrawler
from crawl4ai.chunking_strategy import RegexChunking, FixedLengthWordChunking, SlidingWindowChunking
from crawl4ai.extraction_strategy import CosineStrategy, LLMExtractionStrategy, TopicExtractionStrategy, NoExtractionStrategy

class TestWebCrawler(unittest.TestCase):
    
    def setUp(self):
        self.crawler = WebCrawler()
    
    def test_warmup(self):
        self.crawler.warmup()
        self.assertTrue(self.crawler.ready, "WebCrawler failed to warm up")
    
    def test_run_default_strategies(self):
        result = self.crawler.run(
            url='https://www.nbcnews.com/business',
            word_count_threshold=5,
            chunking_strategy=RegexChunking(),
            extraction_strategy=CosineStrategy(), bypass_cache=True
        )
        self.assertTrue(result.success, "Failed to crawl and extract using default strategies")
    
    def test_run_different_strategies(self):
        url = 'https://www.nbcnews.com/business'
        
        # Test with FixedLengthWordChunking and LLMExtractionStrategy
        result = self.crawler.run(
            url=url,
            word_count_threshold=5,
            chunking_strategy=FixedLengthWordChunking(chunk_size=100),
            extraction_strategy=LLMExtractionStrategy(provider="openai/gpt-3.5-turbo", api_token=os.getenv('OPENAI_API_KEY')), bypass_cache=True
        )
        self.assertTrue(result.success, "Failed to crawl and extract with FixedLengthWordChunking and LLMExtractionStrategy")
        
        # Test with SlidingWindowChunking and TopicExtractionStrategy
        result = self.crawler.run(
            url=url,
            word_count_threshold=5,
            chunking_strategy=SlidingWindowChunking(window_size=100, step=50),
            extraction_strategy=TopicExtractionStrategy(num_keywords=5), bypass_cache=True
        )
        self.assertTrue(result.success, "Failed to crawl and extract with SlidingWindowChunking and TopicExtractionStrategy")
    
    def test_invalid_url(self):
        with self.assertRaises(Exception) as context:
            self.crawler.run(url='invalid_url', bypass_cache=True)
        self.assertIn("Invalid URL", str(context.exception))
    
    def test_unsupported_extraction_strategy(self):
        with self.assertRaises(Exception) as context:
            self.crawler.run(url='https://www.nbcnews.com/business', extraction_strategy="UnsupportedStrategy", bypass_cache=True)
        self.assertIn("Unsupported extraction strategy", str(context.exception))
    
    def test_invalid_css_selector(self):
        with self.assertRaises(ValueError) as context:
            self.crawler.run(url='https://www.nbcnews.com/business', css_selector="invalid_selector", bypass_cache=True)
        self.assertIn("Invalid CSS selector", str(context.exception))

    
    def test_crawl_with_cache_and_bypass_cache(self):
        url = 'https://www.nbcnews.com/business'
        
        # First crawl with cache enabled
        result = self.crawler.run(url=url, bypass_cache=False)
        self.assertTrue(result.success, "Failed to crawl and cache the result")
        
        # Second crawl with bypass_cache=True
        result = self.crawler.run(url=url, bypass_cache=True)
        self.assertTrue(result.success, "Failed to bypass cache and fetch fresh data")
    
    def test_fetch_multiple_pages(self):
        urls = [
            'https://www.nbcnews.com/business',
            'https://www.bbc.com/news'
        ]
        results = []
        for url in urls:
            result = self.crawler.run(
                url=url,
                word_count_threshold=5,
                chunking_strategy=RegexChunking(),
                extraction_strategy=CosineStrategy(),
                bypass_cache=True
            )
            results.append(result)
        
        self.assertEqual(len(results), 2, "Failed to crawl and extract multiple pages")
        for result in results:
            self.assertTrue(result.success, "Failed to crawl and extract a page in the list")
    
    def test_run_fixed_length_word_chunking_and_no_extraction(self):
        result = self.crawler.run(
            url='https://www.nbcnews.com/business',
            word_count_threshold=5,
            chunking_strategy=FixedLengthWordChunking(chunk_size=100),
            extraction_strategy=NoExtractionStrategy(), bypass_cache=True
        )
        self.assertTrue(result.success, "Failed to crawl and extract with FixedLengthWordChunking and NoExtractionStrategy")

    def test_run_sliding_window_and_no_extraction(self):
        result = self.crawler.run(
            url='https://www.nbcnews.com/business',
            word_count_threshold=5,
            chunking_strategy=SlidingWindowChunking(window_size=100, step=50),
            extraction_strategy=NoExtractionStrategy(), bypass_cache=True
        )
        self.assertTrue(result.success, "Failed to crawl and extract with SlidingWindowChunking and NoExtractionStrategy")

if __name__ == '__main__':
    unittest.main()
