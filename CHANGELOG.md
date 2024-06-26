# Changelog

## [0.2.6] - 2024-06-22
### Fixed
- Fix issue #19: Update Dockerfile to ensure compatibility across multiple platforms.

## [0.2.5] - 2024-06-18
### Added
- Added five important hooks to the crawler:
  - on_driver_created: Called when the driver is ready for initializations.
  - before_get_url: Called right before Selenium fetches the URL.
  - after_get_url: Called after Selenium fetches the URL.
  - before_return_html: Called when the data is parsed and ready.
  - on_user_agent_updated: Called when the user changes the user_agent, causing the driver to reinitialize.
- Added an example in `quickstart.py` in the example folder under the docs.
- Enhancement issue #24: Replaced inline HTML tags (e.g., DEL, INS, SUB, ABBR) with textual format for better context handling in LLM.
- Maintaining the semantic context of inline tags (e.g., abbreviation, DEL, INS) for improved LLM-friendliness.
- Updated Dockerfile to ensure compatibility across multiple platforms (Hopefully!).

## [0.2.4] - 2024-06-17
### Fixed
- Fix issue #22: Use MD5 hash for caching HTML files to handle long URLs
## Update 2024-06-26

### Commits in the last 3 hours:
4756d0a - Refactor crawler_strategy.py to handle exceptions and improve error messages
7ba2142 - chore: Refactor get_content_of_website_optimized function in utils.py
96d1eb0 - Some updated ins utils.py
144cfa0 - Switch to ChromeDriverManager due some issues with download the chrome driver
null
null
null
Here is a rewritten version of the changelog update in a nicer and more condensed way:

**Update 2024-06-26**

We've made some exciting improvements to our codebase! Here are the highlights:

* Refactored our crawler strategy to handle exceptions and provide clearer error messages
* Optimized our content retrieval function for improved performance
* Updated internal utilities for better functionality
* Switched to ChromeDriverManager to resolve issues with downloading Chrome drivers

These updates aim to improve stability, reliability, and overall performance. Thank you for using our tool!
Here is a rewritten version of the changelog update:

**June 26, 2024**

We've made some improvements to our code to make it more reliable and user-friendly! 

In the last 3 hours, we've committed 4 changes:

* Improved error handling and messaging in [crawler_strategy.py](https://example.com/crawler_strategy.py)
* Refactored [get_content_of_website_optimized](https://example.com/utils.py) in [utils.py](https://example.com/utils.py)
* Made updates to [utils.py](https://example.com/utils.py)
* Switched to [ChromeDriverManager](https://example.com/ChromeDriverManager) to resolve issues with downloading the Chrome driver.
