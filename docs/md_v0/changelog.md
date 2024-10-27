# Changelog

## [v0.2.77] - 2024-08-04

Significant improvements in text processing and performance:

- 🚀 **Dependency reduction**: Removed dependency on spaCy model for text chunk labeling in cosine extraction strategy.
- 🤖 **Transformer upgrade**: Implemented text sequence classification using a transformer model for labeling text chunks.
- ⚡ **Performance enhancement**: Improved model loading speed due to removal of spaCy dependency.
- 🔧 **Future-proofing**: Laid groundwork for potential complete removal of spaCy dependency in future versions.

These changes address issue #68 and provide a foundation for faster, more efficient text processing in Crawl4AI.

## [v0.2.76] - 2024-08-02

Major improvements in functionality, performance, and cross-platform compatibility! 🚀

- 🐳 **Docker enhancements**: Significantly improved Dockerfile for easy installation on Linux, Mac, and Windows.
- 🌐 **Official Docker Hub image**: Launched our first official image on Docker Hub for streamlined deployment.
- 🔧 **Selenium upgrade**: Removed dependency on ChromeDriver, now using Selenium's built-in capabilities for better compatibility.
- 🖼️ **Image description**: Implemented ability to generate textual descriptions for extracted images from web pages.
- ⚡ **Performance boost**: Various improvements to enhance overall speed and performance.

A big shoutout to our amazing community contributors:
- [@aravindkarnam](https://github.com/aravindkarnam) for developing the textual description extraction feature.
- [@FractalMind](https://github.com/FractalMind) for creating the first official Docker Hub image and fixing Dockerfile errors.
- [@ketonkss4](https://github.com/ketonkss4) for identifying Selenium's new capabilities, helping us reduce dependencies.

Your contributions are driving Crawl4AI forward! 🙌

## [v0.2.75] - 2024-07-19

Minor improvements for a more maintainable codebase:

- 🔄 Fixed typos in `chunking_strategy.py` and `crawler_strategy.py` to improve code readability
- 🔄 Removed `.test_pads/` directory from `.gitignore` to keep our repository clean and organized

These changes may seem small, but they contribute to a more stable and sustainable codebase. By fixing typos and updating our `.gitignore` settings, we're ensuring that our code is easier to maintain and scale in the long run.


## v0.2.74 - 2024-07-08
A slew of exciting updates to improve the crawler's stability and robustness! 🎉

- 💻 **UTF encoding fix**: Resolved the Windows \"charmap\" error by adding UTF encoding.
- 🛡️ **Error handling**: Implemented MaxRetryError exception handling in LocalSeleniumCrawlerStrategy.
- 🧹 **Input sanitization**: Improved input sanitization and handled encoding issues in LLMExtractionStrategy.
- 🚮 **Database cleanup**: Removed existing database file and initialized a new one.

## [v0.2.73] - 2024-07-03

💡 In this release, we've bumped the version to v0.2.73 and refreshed our documentation to ensure you have the best experience with our project.

* Supporting website need "with-head" mode to crawl the website with head.
* Fixing the installation issues for setup.py and dockerfile.
* Resolve multiple issues.

## [v0.2.72] - 2024-06-30

This release brings exciting updates and improvements to our project! 🎉

* 📚 **Documentation Updates**: Our documentation has been revamped to reflect the latest changes and additions.
* 🚀 **New Modes in setup.py**: We've added support for three new modes in setup.py: default, torch, and transformers. This enhances the project's flexibility and usability.
* 🐳 **Docker File Updates**: The Docker file has been updated to ensure seamless compatibility with the new modes and improvements.
* 🕷️ **Temporary Solution for Headless Crawling**: We've implemented a temporary solution to overcome issues with crawling websites in headless mode.

These changes aim to improve the overall user experience, provide more flexibility, and enhance the project's performance. We're thrilled to share these updates with you and look forward to continuing to evolve and improve our project!

## [0.2.71] - 2024-06-26

**Improved Error Handling and Performance** 🚧

* 🚫 Refactored `crawler_strategy.py` to handle exceptions and provide better error messages, making it more robust and reliable.
* 💻 Optimized the `get_content_of_website_optimized` function in `utils.py` for improved performance, reducing potential bottlenecks.
* 💻 Updated `utils.py` with the latest changes, ensuring consistency and accuracy.
* 🚫 Migrated to `ChromeDriverManager` to resolve Chrome driver download issues, providing a smoother user experience.

These changes focus on refining the existing codebase, resulting in a more stable, efficient, and user-friendly experience. With these improvements, you can expect fewer errors and better performance in the crawler strategy and utility functions.

## [0.2.71] - 2024-06-25
### Fixed
- Speed up twice the extraction function.

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
