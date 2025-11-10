import time
import asyncio
from crawl4ai import *


# TODO: the user data directory that includes the capsolver extension
user_data_dir = "/browser-profile/Default1"

"""
The capsolver extension supports more features, such as:
    - Telling the extension when to start solving captcha.
    - Calling functions to check whether the captcha has been solved, etc.
Reference blog: https://docs.capsolver.com/guide/automation-tool-integration/
"""

browser_config = BrowserConfig(
    verbose=True,
    headless=False,
    user_data_dir=user_data_dir,
    use_persistent_context=True,
)

async def main():
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result_initial = await crawler.arun(
            url="https://recaptcha-demo.appspot.com/recaptcha-v2-checkbox.php",
            cache_mode=CacheMode.BYPASS,
            session_id="session_captcha_test"
        )

        # do something later
        time.sleep(300)


if __name__ == "__main__":
    asyncio.run(main())
