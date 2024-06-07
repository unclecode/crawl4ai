
import requests, base64, os

data = {
    "urls": [
        "https://www.nbcnews.com/business"
    ],
    "screenshot": True,
}


# Example of executing a JS script on the page before extracting the content
# data = {
#     "urls": [
#         "https://www.nbcnews.com/business"
#     ],
#     "screenshot": True,
#     'js' : ["""
#     const loadMoreButton = Array.from(document.querySelectorAll('button')).
#     find(button => button.textContent.includes('Load More'));
#     loadMoreButton && loadMoreButton.click();
#     """]
# }

# Example of using a custom extraction strategy
# data = {
#     "urls": [
#         "https://www.nbcnews.com/business"
#     ],
#     "extraction_strategy": "CosineStrategy",
#     "extraction_strategy_args": {
#         "semantic_filter": "inflation rent prices"
#     },
# }

# Example of using LLM to extract content
# data = {
#     "urls": [
#         "https://www.nbcnews.com/business"
#     ],
#     "extraction_strategy": "LLMExtractionStrategy",
#     "extraction_strategy_args": {
#         "provider": "groq/llama3-8b-8192",
#         "api_token": os.environ.get("GROQ_API_KEY"),
#         "instruction": """I am interested in only financial news, 
#         and translate them in French."""
#     },
# }

response = requests.post("https://crawl4ai.com/crawl", json=data) 
result = response.json()['results'][0]

print(result['markdown'])
print(result['cleaned_html'])
print(result['media'])
print(result['extracted_content'])
with open("screenshot.png", "wb") as f:
    f.write(base64.b64decode(result['screenshot']))









