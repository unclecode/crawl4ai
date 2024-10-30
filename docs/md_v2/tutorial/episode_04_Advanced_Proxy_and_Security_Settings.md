# Crawl4AI

## Episode 4: Advanced Proxy and Security Settings

### Quick Intro
Showcase proxy configurations (HTTP, SOCKS5, authenticated proxies). Demo: Use rotating proxies and set custom headers to avoid IP blocking and enhance security.

Here’s a focused outline for the **Proxy and Security Settings** video:

---

### **Proxy & Security Settings**

1) **Why Use Proxies in Web Crawling**:

   - Proxies are essential for bypassing IP-based restrictions, improving anonymity, and managing rate limits.
   - Crawl4AI supports simple proxies, authenticated proxies, and proxy rotation for robust web scraping.

2) **Basic Proxy Setup**:

   - **Using a Simple Proxy**:
     ```python
     # HTTP proxy
     crawler = AsyncWebCrawler(proxy="http://proxy.example.com:8080")
     
     # SOCKS proxy
     crawler = AsyncWebCrawler(proxy="socks5://proxy.example.com:1080")
     ```

3) **Authenticated Proxies**:

   - Use `proxy_config` for proxies requiring a username and password:
     ```python
     proxy_config = {
         "server": "http://proxy.example.com:8080",
         "username": "user",
         "password": "pass"
     }
     crawler = AsyncWebCrawler(proxy_config=proxy_config)
     ```

4) **Rotating Proxies**:

   - Rotating proxies helps avoid IP bans by switching IP addresses for each request:
     ```python
     async def get_next_proxy():
         # Define proxy rotation logic here
         return {"server": "http://next.proxy.com:8080"}
     
     async with AsyncWebCrawler() as crawler:
         for url in urls:
             proxy = await get_next_proxy()
             crawler.update_proxy(proxy)
             result = await crawler.arun(url=url)
     ```
   - This setup periodically switches the proxy for enhanced security and access.

5) **Custom Headers for Additional Security**:

   - Set custom headers to mask the crawler’s identity and avoid detection:
     ```python
     headers = {
         "X-Forwarded-For": "203.0.113.195",
         "Accept-Language": "en-US,en;q=0.9",
         "Cache-Control": "no-cache",
         "Pragma": "no-cache"
     }
     crawler = AsyncWebCrawler(headers=headers)
     ```

6) **Combining Proxies with Magic Mode for Anti-Bot Protection**:

   - For sites with aggressive bot detection, combine `proxy` settings with `magic=True`:
     ```python
     async with AsyncWebCrawler(proxy="http://proxy.example.com:8080", headers={"Accept-Language": "en-US"}) as crawler:
         result = await crawler.arun(
             url="https://example.com",
             magic=True  # Enables anti-detection features
         )
     ```
   - **Magic Mode** automatically enables user simulation, random timing, and browser property masking.

7) **Wrap Up & Next Steps**:

   - Summarize the importance of proxies and anti-detection in accessing restricted content and avoiding bans.
   - Tease the next video: **JavaScript Execution and Handling Dynamic Content** for working with interactive and dynamically loaded pages.

---

This outline provides a practical guide to setting up proxies and security configurations, empowering users to navigate restricted sites while staying undetected.