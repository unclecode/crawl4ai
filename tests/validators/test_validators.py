import pytest
from crawl4ai.validators import (
    URLValidator,
    SSLURLValidator,
    ProxyValidator,
    ValidationException,
)

class TestValidators:

    def testURLValueData(self):
        url_validator = URLValidator()
        url_validator.validate("http://google.com/aaa")
        url_validator.validate("google.com")
        url_validator.validate("https://google.com")
        url_validator.validate("https://google.com:7001")
        url_validator.validate(
            "long-foo_bar-askjdla1023u01_2u3-62532040b2148.looo0000ngurl.com"
        )
        url_validator.validate(
            "https://xxxx.example.com/some.php?aksljdlsa/test.html&id=foo@bar.com"
        )
        url_validator.validate(
            "https://xxxxx.freewebhostmost.com#foo@bar.com"
        )
        with pytest.raises(ValidationException):
            url_validator.validate("http://g=oogle")
        with pytest.raises(ValidationException):
            url_validator.validate("http://google.com/abc test/aa")

    def testProxyValueData(self):
        proxy_validator = ProxyValidator()
        proxy_validator.validate("socks5://127.0.0.1:1080")
        proxy_validator.validate("socks4://127.0.0.1:1080")
        proxy_validator.validate("http://192.168.1.1:8080")
        proxy_validator.validate("https://1.1.1.1:8080")
        proxy_validator.validate("https://google.com:8080")
        proxy_validator.validate("http://user:pass@google.com:8080")
        with pytest.raises(ValidationException):
            # incorrect scheme
            proxy_validator.validate("ftp://test.com")
        with pytest.raises(ValidationException):
            # Without port
            proxy_validator.validate("http://test.com")
        with pytest.raises(ValidationException):
            # don't need path
            proxy_validator.validate("http://test.com:8008/path")

    def testSSLURLValueData(self):
        ssl_url_validator = SSLURLValidator()
        ssl_url_validator.validate("https://google.com")
        ssl_url_validator.validate("https://google.com:7001")
        with pytest.raises(ValidationException):
            # without scheme
            ssl_url_validator.validate("google.com")
        with pytest.raises(ValidationException):
            # incorrect scheme
            ssl_url_validator.validate("ftp://google.com")
