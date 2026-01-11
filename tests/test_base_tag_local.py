import unittest
from crawl4ai.html2text import HTML2Text

class TestBaseTag(unittest.TestCase):
    def test_base_tag_handling(self):
        html_content = """
        <html>
        <head>
            <base href="https://example.com/subdir/">
        </head>
        <body>
            <a href="page.html">Link</a>
        </body>
        </html>
        """
        
        # Initialize parser with a different base (or empty)
        parser = HTML2Text(baseurl="https://override.com/") 
        
        # Feed content
        markdown = parser.handle(html_content)
        
        print(f"Markdown Output: {markdown}")
        
        # Expected: The link should be resolved against the <base> tag
        expected_url = "https://example.com/subdir/page.html"
        
        # Current behavior (bug): It resolves against init baseurl ("https://override.com/page.html")
        # OR if baseurl is empty, it stays relative "page.html"
        
        if expected_url in markdown:
            print("SUCCESS: Base tag respected.")
        else:
            print(f"FAILURE: Base tag ignored. Expected {expected_url} in output.")
            
        self.assertIn(expected_url, markdown)

if __name__ == "__main__":
    unittest.main()
