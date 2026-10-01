import pytest
from yarl import URL

from crawl4ai.async_configs import ProxyConfig
from crawl4ai.async_crawler_strategy import AsyncHTTPCrawlerStrategy


@pytest.mark.parametrize("password", ["plainpass", "p@ss", "p#ss", "pa/ss", "p?ss", "p%41ss"])
def test_proxy_url_roundtrips_credentials(password):
    strategy = AsyncHTTPCrawlerStrategy()
    config = ProxyConfig(server="http://host:8080", username="us:er", password=password)
    url = URL(strategy._format_proxy_url(config))
    assert url.host == "host"
    assert url.port == 8080
    assert url.user == "us:er"
    assert url.password == password
