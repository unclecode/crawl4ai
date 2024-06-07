import requests

data = {
  "urls": [
    "https://www.nbcnews.com/business"
  ],
  "word_count_threshold": 5,
  "screenshot": True
}

response = requests.post("https://crawl4ai.com/crawl", json=data) # OR local host if your run locally 
response_data = response.json()
print(response_data['results'][0].keys())