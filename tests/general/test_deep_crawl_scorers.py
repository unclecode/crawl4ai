from crawl4ai.deep_crawling.scorers import CompositeScorer, ContentTypeScorer, DomainAuthorityScorer, FreshnessScorer, KeywordRelevanceScorer, PathDepthScorer


def test_scorers():
    test_cases = [
        # Keyword Scorer Tests
        {
            "scorer_type": "keyword",
            "config": {
                "keywords": ["python", "blog"],
                "weight": 1.0,
                "case_sensitive": False
            },
            "urls": {
                "https://example.com/python-blog": 0.0,
                "https://example.com/PYTHON-BLOG": 0.0,
                "https://example.com/python-only": 0.5,
                "https://example.com/other": 1.0
            }
        },
        
        # Path Depth Scorer Tests
        {
            "scorer_type": "path_depth",
            "config": {
                "optimal_depth": 2,
                "weight": 1.0
            },
            "urls": {
                "https://example.com/a/b": 0.0,
                "https://example.com/a": 0.5,
                "https://example.com/a/b/c": 0.5,
                "https://example.com": 0.66666667
            }
        },
        
        # Content Type Scorer Tests
        {
            "scorer_type": "content_type",
            "config": {
                "type_weights": {
                    ".html$": 1.0,
                    ".pdf$": 0.8,
                    ".jpg$": 0.6
                },
                "weight": 1.0
            },
            "urls": {
                "https://example.com/doc.html": 0.0,
                "https://example.com/doc.pdf": 0.2,
                "https://example.com/img.jpg": 0.4,
                "https://example.com/other.txt": 1.0
            }
        },
        
        # Freshness Scorer Tests
        {
            "scorer_type": "freshness",
            "config": {
                "weight": 1.0,  # Remove current_year since original doesn't support it
            },
            "urls": {
                "https://example.com/2024/01/post": 0.0,
                "https://example.com/2023/12/post": 0.1,
                "https://example.com/2022/post": 0.2,
                "https://example.com/no-date": 0.5
            }
        },
        
        # Domain Authority Scorer Tests
        {
            "scorer_type": "domain",
            "config": {
                "domain_weights": {
                    "python.org": 1.0,
                    "github.com": 0.8,
                    "medium.com": 0.6
                },
                "default_weight": 0.3,
                "weight": 1.0
            },
            "urls": {
                "https://python.org/about": 0.0,
                "https://github.com/repo": 0.2,
                "https://medium.com/post": 0.4,
                "https://unknown.com": 0.7
            }
        }
    ]

    def create_scorer(scorer_type, config):
        if scorer_type == "keyword":
            return KeywordRelevanceScorer(**config)
        elif scorer_type == "path_depth":
            return PathDepthScorer(**config)
        elif scorer_type == "content_type":
            return ContentTypeScorer(**config)
        elif scorer_type == "freshness":
            return FreshnessScorer(**config,current_year=2024)
        elif scorer_type == "domain":
            return DomainAuthorityScorer(**config)

    def run_accuracy_test():
        print("\nAccuracy Tests:")
        print("-" * 50)
        
        all_passed = True
        for test_case in test_cases:
            print(f"\nTesting {test_case['scorer_type']} scorer:")
            scorer = create_scorer(
                test_case['scorer_type'],
                test_case['config']
            )
            
            for url, expected in test_case['urls'].items():
                score = round(scorer.score(url), 8)
                expected = round(expected, 8)
                
                if abs(score - expected) > 0.00001:
                    print(f"❌ Scorer Failed: URL '{url}'")
                    print(f"   Expected: {expected}, Got: {score}")
                    all_passed = False
                else:
                    print(f"✅ Scorer Passed: URL '{url}'")
                    
                    
        return all_passed

    def run_composite_test():
        print("\nTesting Composite Scorer:")
        print("-" * 50)
        
        # Create test data
        test_urls = {
            "https://python.org/blog/2024/01/new-release.html":0.13333333,
            "https://github.com/repo/old-code.pdf": 0.38,
            "https://unknown.com/random": 0.74
        }
        
        # Create composite scorers with all types
        scorers = []
        
        for test_case in test_cases:
            scorer = create_scorer(
                test_case['scorer_type'],
                test_case['config']
            )
            scorers.append(scorer)
            
        composite = CompositeScorer(scorers, normalize=True)
        
        all_passed = True
        for url, expected in test_urls.items():
            score = round(composite.score(url), 8)
            
            if abs(score - expected) > 0.00001:
                print(f"❌ Composite Failed: URL '{url}'")
                print(f"   Expected: {expected}, Got: {score}")
                all_passed = False
            else:
                print(f"✅ Composite Passed: URL '{url}'")
                
        return all_passed

    # Run tests
    print("Running Scorer Tests...")
    accuracy_passed = run_accuracy_test()
    composite_passed = run_composite_test()
    
    if accuracy_passed and composite_passed:
        print("\n✨ All tests passed!")
        # Note: Already have performance tests in run_scorer_performance_test()
    else:
        print("\n❌ Some tests failed!")

    

if __name__ == "__main__":
    test_scorers()