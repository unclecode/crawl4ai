


import requests, base64

data = {
  "urls": [
    "https://www.nbcnews.com/business"
  ],
  "screenshot": True
}

response = requests.post("https://crawl4ai.com/crawl", json=data) # OR local host if your run locally 
result = response.json()['results'][0]


print(result['markdown'])
print(result['cleaned_html'])
print(result['media'])
print(result['extracted_content'])
with open("screenshot.png", "wb") as f:
    f.write(base64.b64decode(result['screenshot']))




