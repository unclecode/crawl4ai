from typing import TYPE_CHECKING, Union

AsyncWebCrawler = Union['AsyncWebCrawlerType']  # Note the string literal
CrawlerRunConfig = Union['CrawlerRunConfigType']
CrawlResult = Union['CrawlResultType']
RunManyReturn = Union['RunManyReturnType']

if TYPE_CHECKING:
    from . import (
        AsyncWebCrawler as AsyncWebCrawlerType,
        CrawlerRunConfig as CrawlerRunConfigType,
        CrawlResult as CrawlResultType,
        RunManyReturn as RunManyReturnType,
    )