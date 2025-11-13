import asyncio
import capsolver
from crawl4ai import *


# TODO: set your config
# Docs: https://docs.capsolver.com/guide/captcha/awsWaf/
api_key = "CAP-xxxxxxxxxxxxxxxxxxxxx"              # your api key of capsolver
site_url = "https://nft.porsche.com/onboarding@6"  # page url of your target site
cookie_domain = ".nft.porsche.com"                 # the domain name to which you want to apply the cookie
captcha_type = "AntiAwsWafTaskProxyLess"           # type of your target captcha
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

        # get aws waf cookie using capsolver sdk
        solution = capsolver.solve({
            "type": captcha_type,
            "websiteURL": site_url,
        })
        cookie = solution["cookie"]
        print("aws waf cookie:", cookie)

        js_code = """
            document.cookie = \'aws-waf-token=""" + cookie + """;domain=""" + cookie_domain + """;path=/\';
            location.reload();
        """

        wait_condition = """() => {
            return document.title === \'Join Porsche’s journey into Web3\';
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
