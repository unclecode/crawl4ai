import asyncio
import capsolver
from crawl4ai import *


# TODO: set your config
# Docs: https://docs.capsolver.com/guide/captcha/ReCaptchaV2/
api_key = "CAP-xxxxxxxxxxxxxxxxxxxxx"                                      # your api key of capsolver
site_key = "6LfW6wATAAAAAHLqO2pb8bDBahxlMxNdo9g947u9"                      # site key of your target site
site_url = "https://recaptcha-demo.appspot.com/recaptcha-v2-checkbox.php"  # page url of your target site
captcha_type = "ReCaptchaV2TaskProxyLess"                                  # type of your target captcha
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

        # get recaptcha token using capsolver sdk
        solution = capsolver.solve({
            "type": captcha_type,
            "websiteURL": site_url,
            "websiteKey": site_key,
        })
        token = solution["gRecaptchaResponse"]
        print("recaptcha token:", token)

        js_code = """
            const textarea = document.getElementById(\'g-recaptcha-response\');
            if (textarea) {
                textarea.value = \"""" + token + """\";
                document.querySelector(\'button.form-field[type="submit"]\').click();
            }
        """

        wait_condition = """() => {
            const items = document.querySelectorAll(\'h2\');
            return items.length > 1;
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
