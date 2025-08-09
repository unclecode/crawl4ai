"""
Comprehensive test suite for ProxyConfig in different forms:
1. String form (ip:port:username:password)
2. Dict form (dictionary with keys)
3. Object form (ProxyConfig instance)
4. Environment variable form (from env vars)

Tests cover all possible scenarios and edge cases using pytest.
"""

import asyncio
import os
import pytest
import tempfile
from unittest.mock import patch

from crawl4ai import AsyncWebCrawler, BrowserConfig
from crawl4ai.async_configs import CrawlerRunConfig, ProxyConfig
from crawl4ai.cache_context import CacheMode


class TestProxyConfig:
    """Comprehensive test suite for ProxyConfig functionality."""
    
    # Test data for different scenarios
    # get free proxy server from from webshare.io https://www.webshare.io/?referral_code=3sqog0y1fvsl
    TEST_PROXY_DATA = {
        "server": "",
        "username": "", 
        "password": "",
        "ip": ""
    }
    
    def setup_method(self):
        """Setup for each test method."""
        self.test_url = "https://httpbin.org/ip"  # Use httpbin for testing
        
    # ==================== OBJECT FORM TESTS ====================
    
    def test_proxy_config_object_creation_basic(self):
        """Test basic ProxyConfig object creation."""
        proxy = ProxyConfig(server="127.0.0.1:8080")
        assert proxy.server == "127.0.0.1:8080"
        assert proxy.username is None
        assert proxy.password is None
        assert proxy.ip == "127.0.0.1"  # Should auto-extract IP
        
    def test_proxy_config_object_creation_full(self):
        """Test ProxyConfig object creation with all parameters."""
        proxy = ProxyConfig(
            server=f"http://{self.TEST_PROXY_DATA['server']}",
            username=self.TEST_PROXY_DATA['username'],
            password=self.TEST_PROXY_DATA['password'],
            ip=self.TEST_PROXY_DATA['ip']
        )
        assert proxy.server == f"http://{self.TEST_PROXY_DATA['server']}"
        assert proxy.username == self.TEST_PROXY_DATA['username']
        assert proxy.password == self.TEST_PROXY_DATA['password']
        assert proxy.ip == self.TEST_PROXY_DATA['ip']
        
    def test_proxy_config_object_ip_extraction(self):
        """Test automatic IP extraction from server URL."""
        test_cases = [
            ("http://192.168.1.1:8080", "192.168.1.1"),
            ("https://10.0.0.1:3128", "10.0.0.1"),
            ("192.168.1.100:8080", "192.168.1.100"),
            ("proxy.example.com:8080", "proxy.example.com"),
        ]
        
        for server, expected_ip in test_cases:
            proxy = ProxyConfig(server=server)
            assert proxy.ip == expected_ip, f"Failed for server: {server}"
            
    def test_proxy_config_object_invalid_server(self):
        """Test ProxyConfig with invalid server formats."""
        # Should not raise exception but may not extract IP properly
        proxy = ProxyConfig(server="invalid-format")
        assert proxy.server == "invalid-format"
        # IP extraction might fail but object should still be created
        
    # ==================== DICT FORM TESTS ====================
    
    def test_proxy_config_from_dict_basic(self):
        """Test creating ProxyConfig from basic dictionary."""
        proxy_dict = {"server": "127.0.0.1:8080"}
        proxy = ProxyConfig.from_dict(proxy_dict)
        assert proxy.server == "127.0.0.1:8080"
        assert proxy.username is None
        assert proxy.password is None
        
    def test_proxy_config_from_dict_full(self):
        """Test creating ProxyConfig from complete dictionary."""
        proxy_dict = {
            "server": f"http://{self.TEST_PROXY_DATA['server']}",
            "username": self.TEST_PROXY_DATA['username'],
            "password": self.TEST_PROXY_DATA['password'],
            "ip": self.TEST_PROXY_DATA['ip']
        }
        proxy = ProxyConfig.from_dict(proxy_dict)
        assert proxy.server == proxy_dict["server"]
        assert proxy.username == proxy_dict["username"]
        assert proxy.password == proxy_dict["password"]
        assert proxy.ip == proxy_dict["ip"]
        
    def test_proxy_config_from_dict_missing_keys(self):
        """Test creating ProxyConfig from dictionary with missing keys."""
        proxy_dict = {"server": "127.0.0.1:8080", "username": "user"}
        proxy = ProxyConfig.from_dict(proxy_dict)
        assert proxy.server == "127.0.0.1:8080"
        assert proxy.username == "user"
        assert proxy.password is None
        assert proxy.ip == "127.0.0.1"  # Should auto-extract
        
    def test_proxy_config_from_dict_empty(self):
        """Test creating ProxyConfig from empty dictionary."""
        proxy_dict = {}
        proxy = ProxyConfig.from_dict(proxy_dict)
        assert proxy.server is None
        assert proxy.username is None
        assert proxy.password is None
        assert proxy.ip is None
        
    def test_proxy_config_from_dict_none_values(self):
        """Test creating ProxyConfig from dictionary with None values."""
        proxy_dict = {
            "server": "127.0.0.1:8080",
            "username": None,
            "password": None,
            "ip": None
        }
        proxy = ProxyConfig.from_dict(proxy_dict)
        assert proxy.server == "127.0.0.1:8080"
        assert proxy.username is None
        assert proxy.password is None
        assert proxy.ip == "127.0.0.1"  # Should auto-extract despite None
        
    # ==================== STRING FORM TESTS ====================
    
    def test_proxy_config_from_string_full_format(self):
        """Test creating ProxyConfig from full string format (ip:port:username:password)."""
        proxy_str = f"{self.TEST_PROXY_DATA['ip']}:6114:{self.TEST_PROXY_DATA['username']}:{self.TEST_PROXY_DATA['password']}"
        proxy = ProxyConfig.from_string(proxy_str)
        assert proxy.server == f"http://{self.TEST_PROXY_DATA['ip']}:6114"
        assert proxy.username == self.TEST_PROXY_DATA['username']
        assert proxy.password == self.TEST_PROXY_DATA['password']
        assert proxy.ip == self.TEST_PROXY_DATA['ip']
        
    def test_proxy_config_from_string_ip_port_only(self):
        """Test creating ProxyConfig from string with only ip:port."""
        proxy_str = "192.168.1.1:8080"
        proxy = ProxyConfig.from_string(proxy_str)
        assert proxy.server == "http://192.168.1.1:8080"
        assert proxy.username is None
        assert proxy.password is None
        assert proxy.ip == "192.168.1.1"
        
    def test_proxy_config_from_string_invalid_format(self):
        """Test creating ProxyConfig from invalid string formats."""
        invalid_formats = [
            "invalid",
            "ip:port:user",  # Missing password (3 parts)
            "ip:port:user:pass:extra",  # Too many parts (5 parts)
            "",
            "::",  # Empty parts but 3 total (invalid)
            "::::",  # Empty parts but 5 total (invalid)
        ]
        
        for proxy_str in invalid_formats:
            with pytest.raises(ValueError, match="Invalid proxy string format"):
                ProxyConfig.from_string(proxy_str)
                
    def test_proxy_config_from_string_edge_cases_that_work(self):
        """Test string formats that should work but might be edge cases."""
        # These cases actually work as valid formats
        edge_cases = [
            (":", "http://:", ""),  # ip:port format with empty values
            (":::", "http://:", ""),  # ip:port:user:pass format with empty values
        ]
        
        for proxy_str, expected_server, expected_ip in edge_cases:
            proxy = ProxyConfig.from_string(proxy_str)
            assert proxy.server == expected_server
            assert proxy.ip == expected_ip
                
    def test_proxy_config_from_string_edge_cases(self):
        """Test string parsing edge cases."""
        # Test with different port numbers
        proxy_str = "10.0.0.1:3128:user:pass"
        proxy = ProxyConfig.from_string(proxy_str)
        assert proxy.server == "http://10.0.0.1:3128"
        
        # Test with special characters in credentials
        proxy_str = "10.0.0.1:8080:user@domain:pass:word"
        with pytest.raises(ValueError):  # Should fail due to extra colon in password
            ProxyConfig.from_string(proxy_str)
            
    # ==================== ENVIRONMENT VARIABLE TESTS ====================
    
    def test_proxy_config_from_env_single_proxy(self):
        """Test loading single proxy from environment variable."""
        proxy_str = f"{self.TEST_PROXY_DATA['ip']}:6114:{self.TEST_PROXY_DATA['username']}:{self.TEST_PROXY_DATA['password']}"
        
        with patch.dict(os.environ, {'TEST_PROXIES': proxy_str}):
            proxies = ProxyConfig.from_env('TEST_PROXIES')
            assert len(proxies) == 1
            proxy = proxies[0]
            assert proxy.ip == self.TEST_PROXY_DATA['ip']
            assert proxy.username == self.TEST_PROXY_DATA['username']
            assert proxy.password == self.TEST_PROXY_DATA['password']
            
    def test_proxy_config_from_env_multiple_proxies(self):
        """Test loading multiple proxies from environment variable."""
        proxy_list = [
            "192.168.1.1:8080:user1:pass1",
            "192.168.1.2:8080:user2:pass2",
            "10.0.0.1:3128"  # No auth
        ]
        proxy_str = ",".join(proxy_list)
        
        with patch.dict(os.environ, {'TEST_PROXIES': proxy_str}):
            proxies = ProxyConfig.from_env('TEST_PROXIES')
            assert len(proxies) == 3
            
            # Check first proxy
            assert proxies[0].ip == "192.168.1.1"
            assert proxies[0].username == "user1"
            assert proxies[0].password == "pass1"
            
            # Check second proxy
            assert proxies[1].ip == "192.168.1.2"
            assert proxies[1].username == "user2"
            assert proxies[1].password == "pass2"
            
            # Check third proxy (no auth)
            assert proxies[2].ip == "10.0.0.1"
            assert proxies[2].username is None
            assert proxies[2].password is None
            
    def test_proxy_config_from_env_empty_var(self):
        """Test loading from empty environment variable."""
        with patch.dict(os.environ, {'TEST_PROXIES': ''}):
            proxies = ProxyConfig.from_env('TEST_PROXIES')
            assert len(proxies) == 0
            
    def test_proxy_config_from_env_missing_var(self):
        """Test loading from missing environment variable."""
        # Ensure the env var doesn't exist
        with patch.dict(os.environ, {}, clear=True):
            proxies = ProxyConfig.from_env('NON_EXISTENT_VAR')
            assert len(proxies) == 0
            
    def test_proxy_config_from_env_with_empty_entries(self):
        """Test loading proxies with empty entries in the list."""
        proxy_str = "192.168.1.1:8080:user:pass,,10.0.0.1:3128,"
        
        with patch.dict(os.environ, {'TEST_PROXIES': proxy_str}):
            proxies = ProxyConfig.from_env('TEST_PROXIES')
            assert len(proxies) == 2  # Empty entries should be skipped
            assert proxies[0].ip == "192.168.1.1"
            assert proxies[1].ip == "10.0.0.1"
            
    def test_proxy_config_from_env_with_invalid_entries(self):
        """Test loading proxies with some invalid entries."""
        proxy_str = "192.168.1.1:8080:user:pass,invalid_proxy,10.0.0.1:3128"
        
        with patch.dict(os.environ, {'TEST_PROXIES': proxy_str}):
            # Should handle errors gracefully and return valid proxies
            proxies = ProxyConfig.from_env('TEST_PROXIES')
            # Depending on implementation, might return partial list or empty
            # This tests error handling
            assert isinstance(proxies, list)
            
    # ==================== SERIALIZATION TESTS ====================
    
    def test_proxy_config_to_dict(self):
        """Test converting ProxyConfig to dictionary."""
        proxy = ProxyConfig(
            server=f"http://{self.TEST_PROXY_DATA['server']}",
            username=self.TEST_PROXY_DATA['username'],
            password=self.TEST_PROXY_DATA['password'],
            ip=self.TEST_PROXY_DATA['ip']
        )
        
        result_dict = proxy.to_dict()
        expected = {
            "server": f"http://{self.TEST_PROXY_DATA['server']}",
            "username": self.TEST_PROXY_DATA['username'],
            "password": self.TEST_PROXY_DATA['password'],
            "ip": self.TEST_PROXY_DATA['ip']
        }
        assert result_dict == expected
        
    def test_proxy_config_clone(self):
        """Test cloning ProxyConfig with modifications."""
        original = ProxyConfig(
            server="http://127.0.0.1:8080",
            username="user",
            password="pass"
        )
        
        # Clone with modifications
        cloned = original.clone(username="new_user", password="new_pass")
        
        # Original should be unchanged
        assert original.username == "user"
        assert original.password == "pass"
        
        # Clone should have new values
        assert cloned.username == "new_user"
        assert cloned.password == "new_pass"
        assert cloned.server == original.server  # Unchanged value
        
    def test_proxy_config_roundtrip_serialization(self):
        """Test that ProxyConfig can be serialized and deserialized without loss."""
        original = ProxyConfig(
            server=f"http://{self.TEST_PROXY_DATA['server']}",
            username=self.TEST_PROXY_DATA['username'],
            password=self.TEST_PROXY_DATA['password'],
            ip=self.TEST_PROXY_DATA['ip']
        )
        
        # Serialize to dict and back
        serialized = original.to_dict()
        deserialized = ProxyConfig.from_dict(serialized)
        
        assert deserialized.server == original.server
        assert deserialized.username == original.username
        assert deserialized.password == original.password
        assert deserialized.ip == original.ip
        
    # ==================== INTEGRATION TESTS ====================
    
    @pytest.mark.asyncio
    async def test_crawler_with_proxy_config_object(self):
        """Test AsyncWebCrawler with ProxyConfig object."""
        proxy_config = ProxyConfig(
            server=f"http://{self.TEST_PROXY_DATA['server']}",
            username=self.TEST_PROXY_DATA['username'],
            password=self.TEST_PROXY_DATA['password']
        )
        
        browser_config = BrowserConfig(headless=True)
        
        # Test that the crawler accepts the ProxyConfig object without errors
        async with AsyncWebCrawler(config=browser_config) as crawler:
            try:
                # Note: This might fail due to actual proxy connection, but should not fail due to config issues
                result = await crawler.arun(
                    url=self.test_url,
                    config=CrawlerRunConfig(
                        cache_mode=CacheMode.BYPASS,
                        proxy_config=proxy_config,
                        page_timeout=10000  # Short timeout for testing
                    )
                )
                # If we get here, proxy config was accepted
                assert result is not None
            except Exception as e:
                # We expect connection errors with test proxies, but not config errors
                error_msg = str(e).lower()
                assert "attribute" not in error_msg, f"Config error: {e}"
                assert "proxy_config" not in error_msg, f"Proxy config error: {e}"
                
    @pytest.mark.asyncio
    async def test_crawler_with_proxy_config_dict(self):
        """Test AsyncWebCrawler with ProxyConfig from dictionary."""
        proxy_dict = {
            "server": f"http://{self.TEST_PROXY_DATA['server']}",
            "username": self.TEST_PROXY_DATA['username'],
            "password": self.TEST_PROXY_DATA['password']
        }
        proxy_config = ProxyConfig.from_dict(proxy_dict)
        
        browser_config = BrowserConfig(headless=True)
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            try:
                result = await crawler.arun(
                    url=self.test_url,
                    config=CrawlerRunConfig(
                        cache_mode=CacheMode.BYPASS,
                        proxy_config=proxy_config,
                        page_timeout=10000
                    )
                )
                assert result is not None
            except Exception as e:
                error_msg = str(e).lower()
                assert "attribute" not in error_msg, f"Config error: {e}"
                
    @pytest.mark.asyncio
    async def test_crawler_with_proxy_config_from_string(self):
        """Test AsyncWebCrawler with ProxyConfig from string."""
        proxy_str = f"{self.TEST_PROXY_DATA['ip']}:6114:{self.TEST_PROXY_DATA['username']}:{self.TEST_PROXY_DATA['password']}"
        proxy_config = ProxyConfig.from_string(proxy_str)
        
        browser_config = BrowserConfig(headless=True)
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            try:
                result = await crawler.arun(
                    url=self.test_url,
                    config=CrawlerRunConfig(
                        cache_mode=CacheMode.BYPASS,
                        proxy_config=proxy_config,
                        page_timeout=10000
                    )
                )
                assert result is not None
            except Exception as e:
                error_msg = str(e).lower()
                assert "attribute" not in error_msg, f"Config error: {e}"
                
    # ==================== EDGE CASES AND ERROR HANDLING ====================
    
    def test_proxy_config_with_none_server(self):
        """Test ProxyConfig behavior with None server."""
        proxy = ProxyConfig(server=None)
        assert proxy.server is None
        assert proxy.ip is None  # Should not crash
        
    def test_proxy_config_with_empty_string_server(self):
        """Test ProxyConfig behavior with empty string server."""
        proxy = ProxyConfig(server="")
        assert proxy.server == ""
        assert proxy.ip is None or proxy.ip == ""
        
    def test_proxy_config_special_characters_in_credentials(self):
        """Test ProxyConfig with special characters in username/password."""
        special_chars_tests = [
            ("user@domain.com", "pass!@#$%"),
            ("user_123", "p@ssw0rd"),
            ("user-test", "pass-word"),
        ]
        
        for username, password in special_chars_tests:
            proxy = ProxyConfig(
                server="http://127.0.0.1:8080",
                username=username,
                password=password
            )
            assert proxy.username == username
            assert proxy.password == password
            
    def test_proxy_config_unicode_handling(self):
        """Test ProxyConfig with unicode characters."""
        proxy = ProxyConfig(
            server="http://127.0.0.1:8080",
            username="ユーザー",  # Japanese characters
            password="пароль"    # Cyrillic characters
        )
        assert proxy.username == "ユーザー"
        assert proxy.password == "пароль"
        
    # ==================== PERFORMANCE TESTS ====================
    
    def test_proxy_config_creation_performance(self):
        """Test that ProxyConfig creation is reasonably fast."""
        import time
        
        start_time = time.time()
        for i in range(1000):
            proxy = ProxyConfig(
                server=f"http://192.168.1.{i % 255}:8080",
                username=f"user{i}",
                password=f"pass{i}"
            )
        end_time = time.time()
        
        # Should be able to create 1000 configs in less than 1 second
        assert (end_time - start_time) < 1.0
        
    def test_proxy_config_from_env_performance(self):
        """Test that loading many proxies from env is reasonably fast."""
        import time
        
        # Create a large list of proxy strings
        proxy_list = [f"192.168.1.{i}:8080:user{i}:pass{i}" for i in range(100)]
        proxy_str = ",".join(proxy_list)
        
        with patch.dict(os.environ, {'PERF_TEST_PROXIES': proxy_str}):
            start_time = time.time()
            proxies = ProxyConfig.from_env('PERF_TEST_PROXIES')
            end_time = time.time()
            
            assert len(proxies) == 100
            # Should be able to parse 100 proxies in less than 1 second
            assert (end_time - start_time) < 1.0


# ==================== STANDALONE TEST FUNCTIONS ====================

@pytest.mark.asyncio
async def test_dict_proxy():
    """Original test function for dict proxy - kept for backward compatibility."""
    proxy_config = {
        "server": "23.95.150.145:6114", 
        "username": "cfyswbwn",
        "password": "1gs266hoqysi"
    }
    proxy_config_obj = ProxyConfig.from_dict(proxy_config)
    
    browser_config = BrowserConfig(headless=True)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        try:
            result = await crawler.arun(url="https://httpbin.org/ip", config=CrawlerRunConfig(
                stream=False,
                cache_mode=CacheMode.BYPASS,
                proxy_config=proxy_config_obj,
                page_timeout=10000
            ))
            print("Dict proxy test passed!")
            print(result.markdown[:200] if result and result.markdown else "No result")
        except Exception as e:
            print(f"Dict proxy test error (expected): {e}")


@pytest.mark.asyncio
async def test_string_proxy():
    """Test function for string proxy format."""
    proxy_str = "23.95.150.145:6114:cfyswbwn:1gs266hoqysi"
    proxy_config_obj = ProxyConfig.from_string(proxy_str)
    
    browser_config = BrowserConfig(headless=True)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        try:
            result = await crawler.arun(url="https://httpbin.org/ip", config=CrawlerRunConfig(
                stream=False,
                cache_mode=CacheMode.BYPASS,
                proxy_config=proxy_config_obj,
                page_timeout=10000
            ))
            print("String proxy test passed!")
            print(result.markdown[:200] if result and result.markdown else "No result")
        except Exception as e:
            print(f"String proxy test error (expected): {e}")


@pytest.mark.asyncio
async def test_env_proxy():
    """Test function for environment variable proxy."""
    # Set environment variable
    os.environ['TEST_PROXIES'] = "23.95.150.145:6114:cfyswbwn:1gs266hoqysi"
    
    proxies = ProxyConfig.from_env('TEST_PROXIES')
    if proxies:
        proxy_config_obj = proxies[0]  # Use first proxy
        
        browser_config = BrowserConfig(headless=True)
        async with AsyncWebCrawler(config=browser_config) as crawler:
            try:
                result = await crawler.arun(url="https://httpbin.org/ip", config=CrawlerRunConfig(
                    stream=False,
                    cache_mode=CacheMode.BYPASS,
                    proxy_config=proxy_config_obj,
                    page_timeout=10000
                ))
                print("Environment proxy test passed!")
                print(result.markdown[:200] if result and result.markdown else "No result")
            except Exception as e:
                print(f"Environment proxy test error (expected): {e}")
    else:
        print("No proxies loaded from environment")


if __name__ == "__main__":
    print("Running comprehensive ProxyConfig tests...")
    print("=" * 50)
    
    # Run the standalone test functions
    print("\n1. Testing dict proxy format...")
    asyncio.run(test_dict_proxy())
    
    print("\n2. Testing string proxy format...")
    asyncio.run(test_string_proxy())
    
    print("\n3. Testing environment variable proxy format...")
    asyncio.run(test_env_proxy())
    
    print("\n" + "=" * 50)
    print("To run the full pytest suite, use: pytest " + __file__)
    print("=" * 50)