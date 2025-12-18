import asyncio
import capsolver
from crawl4ai import *


# TODO: set your config
# Docs: https://docs.capsolver.com/guide/captcha/cloudflare_turnstile/
api_key = "CAP-xxxxxxxxxxxxxxxxxxxxx"                       # your api key of capsolver
site_key = "0x4AAAAAAAGlwMzq_9z6S9Mh"                       # site key of your target site
site_url = "https://clifford.io/demo/cloudflare-turnstile"  # page url of your target site
captcha_type = "AntiTurnstileTaskProxyLess"                 # type of your target captcha
capsolver.api_key = api_key


async def main():
    browser_config = BrowserConfig(
        verbose=True,
        headless=False,
        use_persistent_context=True,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        await crawler.arun(
            url=site_url,
            cache_mode=CacheMode.BYPASS,
            session_id="session_captcha_test"
        )

        # get turnstile token using capsolver sdk
        solution = capsolver.solve({
            "type": captcha_type,
            "websiteURL": site_url,
            "websiteKey": site_key,
        })
        token = solution["token"]
        print("turnstile token:", token)

        js_code = """
            document.querySelector(\'input[name="cf-turnstile-response"]\').value = \'"""+token+"""\';
            document.querySelector(\'button[type="submit"]\').click();
        """

        wait_condition = """() => {
            const items = document.querySelectorAll(\'h1\');
            return items.length === 0;
        }"""

        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            session_id="session_captcha_test",
            js_code=js_code,
            js_only=True,
            wait_for=f"js:{wait_condition}"
        )

        result_next = await crawler.arun(
            url=site_url,
            config=run_config,
        )
        print(result_next.markdown)


if __name__ == "__main__":
    asyncio.run(main())
