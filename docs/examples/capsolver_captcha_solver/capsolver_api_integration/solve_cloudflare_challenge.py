import asyncio
import capsolver
from crawl4ai import *


# TODO: set your config
# Docs: https://docs.capsolver.com/guide/captcha/cloudflare_challenge/
api_key = "CAP-xxxxxxxxxxxxxxxxxxxxx"          # your api key of capsolver
site_url = "https://gitlab.com/users/sign_in"  # page url of your target site
captcha_type = "AntiCloudflareTask"            # type of your target captcha
# your http proxy to solve cloudflare challenge
proxy_server = "proxy.example.com:8080"
proxy_username = "myuser"
proxy_password = "mypass"
capsolver.api_key = api_key


async def main():
    # get challenge cookie using capsolver sdk
    solution = capsolver.solve({
        "type": captcha_type,
        "websiteURL": site_url,
        "proxy": f"{proxy_server}:{proxy_username}:{proxy_password}",
    })
    cookies = solution["cookies"]
    user_agent = solution["userAgent"]
    print("challenge cookies:", cookies)

    cookies_list = []
    for name, value in cookies.items():
        cookies_list.append({
            "name": name,
            "value": value,
            "url": site_url,
        })

    browser_config = BrowserConfig(
        verbose=True,
        headless=False,
        use_persistent_context=True,
        user_agent=user_agent,
        cookies=cookies_list,
        proxy_config={
            "server": f"http://{proxy_server}",
            "username": proxy_username,
            "password": proxy_password,
        },
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=site_url,
            cache_mode=CacheMode.BYPASS,
            session_id="session_captcha_test"
        )
        print(result.markdown)


if __name__ == "__main__":
    asyncio.run(main())
