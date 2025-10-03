import sqlite3
import json
import random
from datetime import datetime, timedelta
from database import DatabaseManager

def generate_slug(text):
    return text.lower().replace(' ', '-').replace('&', 'and')

def generate_dummy_data():
    db = DatabaseManager()
    conn = db.conn
    cursor = conn.cursor()

    # Clear existing data
    for table in ['apps', 'articles', 'categories', 'sponsors']:
        cursor.execute(f"DELETE FROM {table}")

    # Categories
    categories = [
        ("Browser Automation", "⚙", "Tools for browser automation and control"),
        ("Proxy Services", "🔒", "Proxy providers and rotation services"),
        ("LLM Integration", "🤖", "AI/LLM tools and integrations"),
        ("Data Processing", "📊", "Data extraction and processing tools"),
        ("Cloud Infrastructure", "☁", "Cloud browser and computing services"),
        ("Developer Tools", "🛠", "Development and testing utilities")
    ]

    for i, (name, icon, desc) in enumerate(categories):
        cursor.execute("""
            INSERT INTO categories (name, slug, icon, description, order_index)
            VALUES (?, ?, ?, ?, ?)
        """, (name, generate_slug(name), icon, desc, i))

    # Apps with real Unsplash images
    apps_data = [
        # Browser Automation
        ("Playwright Cloud", "Browser Automation", "Paid", True, True,
         "Scalable browser automation in the cloud with Playwright", "https://playwright.cloud",
         None, "$99/month starter", 4.8, 12500,
         "https://images.unsplash.com/photo-1633356122544-f134324a6cee?w=800&h=400&fit=crop"),

        ("Selenium Grid Hub", "Browser Automation", "Freemium", False, False,
         "Distributed Selenium grid for parallel testing", "https://seleniumhub.io",
         "https://github.com/seleniumhub/grid", "Free - $299/month", 4.2, 8400,
         "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=800&h=400&fit=crop"),

        ("Puppeteer Extra", "Browser Automation", "Open Source", True, False,
         "Enhanced Puppeteer with stealth plugins and more", "https://puppeteer-extra.dev",
         "https://github.com/berstend/puppeteer-extra", "Free", 4.6, 15200,
         "https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=800&h=400&fit=crop"),

        # Proxy Services
        ("BrightData", "Proxy Services", "Paid", True, True,
         "Premium proxy network with 72M+ IPs worldwide", "https://brightdata.com",
         None, "Starting $500/month", 4.7, 9800,
         "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&h=400&fit=crop"),

        ("SmartProxy", "Proxy Services", "Paid", False, True,
         "Residential and datacenter proxies with rotation", "https://smartproxy.com",
         None, "Starting $75/month", 4.3, 7600,
         "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=800&h=400&fit=crop"),

        ("ProxyMesh", "Proxy Services", "Freemium", False, False,
         "Rotating proxy servers with sticky sessions", "https://proxymesh.com",
         None, "$10-$50/month", 4.0, 4200,
         "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&h=400&fit=crop"),

        # LLM Integration
        ("LangChain Crawl", "LLM Integration", "Open Source", True, False,
         "LangChain integration for Crawl4AI workflows", "https://langchain-crawl.dev",
         "https://github.com/langchain/crawl", "Free", 4.5, 18900,
         "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800&h=400&fit=crop"),

        ("GPT Scraper", "LLM Integration", "Freemium", False, False,
         "Extract structured data using GPT models", "https://gptscraper.ai",
         None, "Free - $99/month", 4.1, 5600,
         "https://images.unsplash.com/photo-1655720828018-edd2daec9349?w=800&h=400&fit=crop"),

        ("Claude Extract", "LLM Integration", "Paid", True, True,
         "Professional extraction using Claude AI", "https://claude-extract.com",
         None, "$199/month", 4.9, 3200,
         "https://images.unsplash.com/photo-1686191128892-3b09ad503b4f?w=800&h=400&fit=crop"),

        # Data Processing
        ("DataMiner Pro", "Data Processing", "Paid", False, False,
         "Advanced data extraction and transformation", "https://dataminer.pro",
         None, "$149/month", 4.2, 6700,
         "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&h=400&fit=crop"),

        ("ScraperAPI", "Data Processing", "Freemium", True, True,
         "Simple API for web scraping with proxy rotation", "https://scraperapi.com",
         None, "Free - $299/month", 4.6, 22300,
         "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&h=400&fit=crop"),

        ("Apify", "Data Processing", "Freemium", False, False,
         "Web scraping and automation platform", "https://apify.com",
         None, "$49-$499/month", 4.4, 14500,
         "https://images.unsplash.com/photo-1504639725590-34d0984388bd?w=800&h=400&fit=crop"),

        # Cloud Infrastructure
        ("BrowserCloud", "Cloud Infrastructure", "Paid", True, True,
         "Managed headless browsers in the cloud", "https://browsercloud.io",
         None, "$199/month", 4.5, 8900,
         "https://images.unsplash.com/photo-1667372393119-3d4c48d07fc9?w=800&h=400&fit=crop"),

        ("LambdaTest", "Cloud Infrastructure", "Freemium", False, False,
         "Cross-browser testing on cloud", "https://lambdatest.com",
         None, "Free - $99/month", 4.1, 11200,
         "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&h=400&fit=crop"),

        ("Browserless", "Cloud Infrastructure", "Freemium", True, False,
         "Headless browser automation API", "https://browserless.io",
         None, "$50-$500/month", 4.7, 19800,
         "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=800&h=400&fit=crop"),

        # Developer Tools
        ("Crawl4AI VSCode", "Developer Tools", "Open Source", True, False,
         "VSCode extension for Crawl4AI development", "https://marketplace.visualstudio.com",
         "https://github.com/crawl4ai/vscode", "Free", 4.8, 34500,
         "https://images.unsplash.com/photo-1629654297299-c8506221ca97?w=800&h=400&fit=crop"),

        ("Postman Collection", "Developer Tools", "Open Source", False, False,
         "Postman collection for Crawl4AI API testing", "https://postman.com/crawl4ai",
         "https://github.com/crawl4ai/postman", "Free", 4.3, 7800,
         "https://images.unsplash.com/photo-1599507593499-a3f7d7d97667?w=800&h=400&fit=crop"),

        ("Debug Toolkit", "Developer Tools", "Open Source", False, False,
         "Debugging tools for crawler development", "https://debug.crawl4ai.com",
         "https://github.com/crawl4ai/debug", "Free", 4.0, 4300,
         "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?w=800&h=400&fit=crop"),
    ]

    for name, category, type_, featured, sponsored, desc, url, github, pricing, rating, downloads, image in apps_data:
        screenshots = json.dumps([
            f"https://images.unsplash.com/photo-{random.randint(1500000000000, 1700000000000)}-{random.randint(1000000000000, 9999999999999)}?w=800&h=600&fit=crop",
            f"https://images.unsplash.com/photo-{random.randint(1500000000000, 1700000000000)}-{random.randint(1000000000000, 9999999999999)}?w=800&h=600&fit=crop"
        ])
        cursor.execute("""
            INSERT INTO apps (name, slug, description, category, type, featured, sponsored,
                            website_url, github_url, pricing, rating, downloads, image, screenshots, logo_url,
                            integration_guide, contact_email, views)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, generate_slug(name), desc, category, type_, featured, sponsored,
             url, github, pricing, rating, downloads, image, screenshots,
             f"https://ui-avatars.com/api/?name={name}&background=50ffff&color=070708&size=128",
             f"# {name} Integration\n\n```python\nfrom crawl4ai import AsyncWebCrawler\n# Integration code coming soon...\n```",
             f"contact@{generate_slug(name)}.com",
             random.randint(100, 5000)))

    # Articles with real images
    articles_data = [
        ("Browser Automation Showdown: Playwright vs Puppeteer vs Selenium",
         "Review", "John Doe", ["Playwright Cloud", "Puppeteer Extra"],
         ["browser-automation", "comparison", "2024"],
         "https://images.unsplash.com/photo-1587620962725-abab7fe55159?w=1200&h=630&fit=crop"),

        ("Top 5 Proxy Services for Web Scraping in 2024",
         "Comparison", "Jane Smith", ["BrightData", "SmartProxy", "ProxyMesh"],
         ["proxy", "web-scraping", "guide"],
         "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=1200&h=630&fit=crop"),

        ("Integrating LLMs with Crawl4AI: A Complete Guide",
         "Tutorial", "Crawl4AI Team", ["LangChain Crawl", "GPT Scraper", "Claude Extract"],
         ["llm", "integration", "tutorial"],
         "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=1200&h=630&fit=crop"),

        ("Building Scalable Crawlers with Cloud Infrastructure",
         "Tutorial", "Mike Johnson", ["BrowserCloud", "Browserless"],
         ["cloud", "scalability", "architecture"],
         "https://images.unsplash.com/photo-1667372393119-3d4c48d07fc9?w=1200&h=630&fit=crop"),

        ("What's New in Crawl4AI Marketplace",
         "News", "Crawl4AI Team", [],
         ["marketplace", "announcement", "news"],
         "https://images.unsplash.com/photo-1556075798-4825dfaaf498?w=1200&h=630&fit=crop"),

        ("Cost Analysis: Self-Hosted vs Cloud Browser Solutions",
         "Comparison", "Sarah Chen", ["BrowserCloud", "LambdaTest", "Browserless"],
         ["cost", "cloud", "comparison"],
         "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=1200&h=630&fit=crop"),

        ("Getting Started with Browser Automation",
         "Tutorial", "Crawl4AI Team", ["Playwright Cloud", "Selenium Grid Hub"],
         ["beginner", "tutorial", "automation"],
         "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=1200&h=630&fit=crop"),

        ("The Future of Web Scraping: AI-Powered Extraction",
         "News", "Dr. Alan Turing", ["Claude Extract", "GPT Scraper"],
         ["ai", "future", "trends"],
         "https://images.unsplash.com/photo-1593720213428-28a5b9e94613?w=1200&h=630&fit=crop")
    ]

    for title, category, author, related_apps, tags, image in articles_data:
        # Get app IDs for related apps
        related_ids = []
        for app_name in related_apps:
            cursor.execute("SELECT id FROM apps WHERE name = ?", (app_name,))
            result = cursor.fetchone()
            if result:
                related_ids.append(result[0])

        content = f"""# {title}

By {author} | {datetime.now().strftime('%B %d, %Y')}

## Introduction

This is a comprehensive article about {title.lower()}. Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

## Key Points

- Important point about the topic
- Another crucial insight
- Technical details and specifications
- Performance comparisons

## Conclusion

In summary, this article explored various aspects of the topic. Stay tuned for more updates!
"""

        cursor.execute("""
            INSERT INTO articles (title, slug, content, author, category, related_apps,
                                featured_image, tags, views)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, generate_slug(title), content, author, category,
             json.dumps(related_ids), image, json.dumps(tags),
             random.randint(200, 10000)))

    # Sponsors
    sponsors_data = [
        ("BrightData", "Gold", "https://brightdata.com",
         "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=728&h=90&fit=crop"),
        ("ScraperAPI", "Gold", "https://scraperapi.com",
         "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=728&h=90&fit=crop"),
        ("BrowserCloud", "Silver", "https://browsercloud.io",
         "https://images.unsplash.com/photo-1667372393119-3d4c48d07fc9?w=728&h=90&fit=crop"),
        ("Claude Extract", "Silver", "https://claude-extract.com",
         "https://images.unsplash.com/photo-1686191128892-3b09ad503b4f?w=728&h=90&fit=crop"),
        ("SmartProxy", "Bronze", "https://smartproxy.com",
         "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=728&h=90&fit=crop")
    ]

    for company, tier, landing_url, banner in sponsors_data:
        start_date = datetime.now() - timedelta(days=random.randint(1, 30))
        end_date = datetime.now() + timedelta(days=random.randint(30, 180))

        cursor.execute("""
            INSERT INTO sponsors (company_name, logo_url, tier, banner_url,
                                landing_url, active, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (company,
             f"https://ui-avatars.com/api/?name={company}&background=09b5a5&color=fff&size=200",
             tier, banner, landing_url, 1,
             start_date.isoformat(), end_date.isoformat()))

    conn.commit()
    print("✓ Dummy data generated successfully!")
    print(f"  - {len(categories)} categories")
    print(f"  - {len(apps_data)} apps")
    print(f"  - {len(articles_data)} articles")
    print(f"  - {len(sponsors_data)} sponsors")

if __name__ == "__main__":
    generate_dummy_data()