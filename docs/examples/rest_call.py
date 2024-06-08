
import requests, base64, os

data = {
    "urls": ["https://www.nbcnews.com/business"],
    "screenshot": True,
}

response = requests.post("https://crawl4ai.com/crawl", json=data) 
result = response.json()['results'][0]
print(result.keys())
# dict_keys(['url', 'html', 'success', 'cleaned_html', 'media', 
# 'links', 'screenshot', 'markdown', 'extracted_content', 
# 'metadata', 'error_message'])
with open("screenshot.png", "wb") as f:
    f.write(base64.b64decode(result['screenshot']))
    
# Example of filtering the content using CSS selectors
data = {
    "urls": [
        "https://www.nbcnews.com/business"
    ],
    "css_selector": "article",
    "screenshot": True,
}

# Example of executing a JS script on the page before extracting the content
data = {
    "urls": [
        "https://www.nbcnews.com/business"
    ],
    "screenshot": True,
    'js' : ["""
    const loadMoreButton = Array.from(document.querySelectorAll('button')).
    find(button => button.textContent.includes('Load More'));
    loadMoreButton && loadMoreButton.click();
    """]
}

# Example of using a custom extraction strategy
data = {
    "urls": [
        "https://www.nbcnews.com/business"
    ],
    "extraction_strategy": "CosineStrategy",
    "extraction_strategy_args": {
        "semantic_filter": "inflation rent prices"
    },
}

# Example of using LLM to extract content
data = {
    "urls": [
        "https://www.nbcnews.com/business"
    ],
    "extraction_strategy": "LLMExtractionStrategy",
    "extraction_strategy_args": {
        "provider": "groq/llama3-8b-8192",
        "api_token": os.environ.get("GROQ_API_KEY"),
        "instruction": """I am interested in only financial news, 
        and translate them in French."""
    },
}

