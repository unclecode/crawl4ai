# Contributors to Crawl4AI

We would like to thank the following people for their contributions to Crawl4AI:

## Core Team

- [Unclecode](https://github.com/unclecode) - Project Creator and Main Developer
- [Nasrin](https://github.com/ntohidi) - Project Manager and Developer
- [Aravind Karnam](https://github.com/aravindkarnam) - Head of Community and Product 

## Community Contributors

- [aadityakanjolia4](https://github.com/aadityakanjolia4) - Fix for `CustomHTML2Text` is not defined.
- [FractalMind](https://github.com/FractalMind) - Created the first official Docker Hub image and fixed Dockerfile errors
- [ketonkss4](https://github.com/ketonkss4) - Identified Selenium's new capabilities, helping reduce dependencies
- [jonymusky](https://github.com/jonymusky) - Javascript execution documentation, and wait_for
- [datehoer](https://github.com/datehoer) - Add browser prxy support

## Pull Requests

- [dvschuyl](https://github.com/dvschuyl) - AsyncPlaywrightCrawlerStrategy page-evaluate context destroyed by navigation [#304](https://github.com/unclecode/crawl4ai/pull/304)
- [nelzomal](https://github.com/nelzomal) - Enhance development installation instructions [#286](https://github.com/unclecode/crawl4ai/pull/286)
- [HamzaFarhan](https://github.com/HamzaFarhan) - Handled the cases where markdown_with_citations, references_markdown, and filtered_html might not be defined [#293](https://github.com/unclecode/crawl4ai/pull/293)
- [NanmiCoder](https://github.com/NanmiCoder) - fix: crawler strategy exception handling and fixes [#271](https://github.com/unclecode/crawl4ai/pull/271)
- [paulokuong](https://github.com/paulokuong) - fix: RAWL4_AI_BASE_DIRECTORY should be Path object instead of string [#298](https://github.com/unclecode/crawl4ai/pull/298)
- [TheRedRad](https://github.com/theredrad) - feat: add force viewport screenshot option [#1694](https://github.com/unclecode/crawl4ai/pull/1694)
- [ChiragBellara](https://github.com/ChiragBellara) - fix: avoid Common Crawl calls for sitemap-only URL seeding [#1746](https://github.com/unclecode/crawl4ai/pull/1746)
- [YuriNachos](https://github.com/YuriNachos) - fix: replace tf-playwright-stealth with playwright-stealth [#1714](https://github.com/unclecode/crawl4ai/pull/1714), fix: respect `<base>` tag for relative link resolution [#1721](https://github.com/unclecode/crawl4ai/pull/1721), fix: include GoogleSearchCrawler script.js in package [#1719](https://github.com/unclecode/crawl4ai/pull/1719), fix: allow local embeddings by removing OpenAI fallback [#1717](https://github.com/unclecode/crawl4ai/pull/1717)
- [christian-oudard](https://github.com/christian-oudard) - fix: deep-crawl CLI outputting only the first page [#1667](https://github.com/unclecode/crawl4ai/pull/1667)
- [vladmandic](https://github.com/vladmandic) - fix: VersionManager ignoring CRAWL4_AI_BASE_DIRECTORY env var [#1296](https://github.com/unclecode/crawl4ai/pull/1296)
- [nnxiong](https://github.com/nnxiong) - fix: script tag removal losing adjacent text in cleaned_html [#1364](https://github.com/unclecode/crawl4ai/pull/1364)
- [RoyLeviLangware](https://github.com/RoyLeviLangware) - fix: bs4 deprecation warning (text -> string) [#1077](https://github.com/unclecode/crawl4ai/pull/1077)
- [garyluky](https://github.com/garyluky) - fix: proxy auth ERR_INVALID_AUTH_CREDENTIALS [#1281](https://github.com/unclecode/crawl4ai/pull/1281)
- [Martichou](https://github.com/Martichou) - investigation: browser context memory leak under continuous load [#1640](https://github.com/unclecode/crawl4ai/pull/1640), [#943](https://github.com/unclecode/crawl4ai/issues/943)
- [danyQe](https://github.com/danyQe) - identified: temperature typo in async_configs.py [#973](https://github.com/unclecode/crawl4ai/pull/973)
- [saipavanmeruga7797](https://github.com/saipavanmeruga7797) - identified: local HTML file crawling bug with capture_console_messages [#1073](https://github.com/unclecode/crawl4ai/pull/1073)
- [stevenaldinger](https://github.com/stevenaldinger) - identified: duplicate PROMPT_EXTRACT_BLOCKS dead code in prompts.py [#931](https://github.com/unclecode/crawl4ai/pull/931)
- [chrizzly2309](https://github.com/chrizzly2309) - identified: JWT auth bypass when no credentials provided [#1133](https://github.com/unclecode/crawl4ai/pull/1133)
- [complete-dope](https://github.com/complete-dope) - identified: console logging error attribute issue [#729](https://github.com/unclecode/crawl4ai/pull/729)
- [TristanDonze](https://github.com/TristanDonze) - feat: add configurable device_scale_factor for screenshot quality [#1463](https://github.com/unclecode/crawl4ai/pull/1463)
- [charlaie](https://github.com/charlaie) - feat: add redirected_status_code to CrawlResult [#1435](https://github.com/unclecode/crawl4ai/pull/1435)
- [mzyfree](https://github.com/mzyfree) - investigation: Docker concurrency performance and pool resource management [#1689](https://github.com/unclecode/crawl4ai/pull/1689)
- [nightcityblade](https://github.com/nightcityblade) - fix: prevent AdaptiveCrawler from crawling external domains [#1805](https://github.com/unclecode/crawl4ai/pull/1805)
- [Otman404](https://github.com/Otman404) - fix: return in finally block silently suppressing exceptions in dispatcher [#1763](https://github.com/unclecode/crawl4ai/pull/1763)
- [SohamKukreti](https://github.com/SohamKukreti) - fix: from_serializable_dict ignoring plain data dicts with "type" key [#1803](https://github.com/unclecode/crawl4ai/pull/1803)

#### Feb-Alpha-1
- [sufianuddin](https://github.com/sufianuddin) - fix: [Documentation for JsonCssExtractionStrategy](https://github.com/unclecode/crawl4ai/issues/651)
- [tautikAg](https://github.com/tautikAg) - fix: [Markdown output has incorect spacing](https://github.com/unclecode/crawl4ai/issues/599)
- [cardit1](https://github.com/cardit1) - fix: ['AsyncPlaywrightCrawlerStrategy' object has no attribute 'downloads_path'](https://github.com/unclecode/crawl4ai/issues/585)
- [dmurat](https://github.com/dmurat) - fix: [ Incorrect rendering of inline code inside of links ](https://github.com/unclecode/crawl4ai/issues/583)
- [Sparshsing](https://github.com/Sparshsing) - fix: [Relative Urls in the webpage not extracted properly ](https://github.com/unclecode/crawl4ai/issues/570)



## Other Contributors

- [Gokhan](https://github.com/gkhngyk) 
- [Shiv Kumar](https://github.com/shivkumar0757)
- [QIN2DIM](https://github.com/QIN2DIM)

#### Typo fixes
- [ssoydan](https://github.com/ssoydan)
- [Darshan](https://github.com/Darshan2104)
- [tuhinmallick](https://github.com/tuhinmallick)

## Acknowledgements

We also want to thank all the users who have reported bugs, suggested features, or helped in any other way to make Crawl4AI better.

---

If you've contributed to Crawl4AI and your name isn't on this list, please [open a pull request](https://github.com/unclecode/crawl4ai/pulls) with your name, link, and contribution, and we'll review it promptly.

Thank you all for your contributions!