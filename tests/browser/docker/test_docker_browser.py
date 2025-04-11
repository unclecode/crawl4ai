"""Test examples for Docker Browser Strategy.

These examples demonstrate the functionality of Docker Browser Strategy
and serve as functional tests.
"""

import asyncio
import sys
import uuid
from asyncio.subprocess import Process
from pathlib import Path
from typing import Any, Optional

import pytest
from playwright.async_api import Response

from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_logger import AsyncLogger
from crawl4ai.browser import BrowserManager
from crawl4ai.browser.docker_config import DockerConfig
from crawl4ai.browser.docker_registry import DockerRegistry
from crawl4ai.browser.docker_strategy import DockerBrowserStrategy
from crawl4ai.browser.docker_utils import DockerUtils
from crawl4ai.browser.strategies import BaseBrowserStrategy

TEST_REGISTRY_FILE = "test_registry.json"

@pytest.fixture
async def skipif_docker_unavailable():
    """Skips the test if docker is unavailable."""
    available: bool = False
    try:
        process: Process = await asyncio.create_subprocess_exec(
            "docker", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout: bytes
        stdout, _ = await process.communicate()
        available = process.returncode == 0 and len(stdout) != 0
    except Exception:
        pass

    if not available:
        pytest.skip("Docker is not available on this system")

@pytest.fixture
def docker_utils() -> DockerUtils:
    """Return a DockerUtils instance."""
    logger: AsyncLogger = AsyncLogger(verbose=True, log_file=None)
    return DockerUtils(logger)

class DockerRegistryFixture(DockerRegistry):
    """Fixture for DockerRegistry to be used in tests.
    This class initializes a DockerRegistry instance with a test file
    and registers a test container.

    :param tmp_path: Temporary path for the test registry file.
    :type tmp_path: Path
    """
    def __init__(self, tmp_path: Path):
        self.container_id: str = "test-container-123"
        self.port: int = 9876
        self.hash: str = "test-hash-123"
        self.file: str = str(tmp_path / TEST_REGISTRY_FILE)
        super().__init__(self.file)
        self.register_container(self.container_id, self.port, self.hash)
        self.save()

@pytest.fixture
def registry(tmp_path: Path) -> DockerRegistryFixture:
    """Create a Docker registry instance for testing."""
    return DockerRegistryFixture(tmp_path)

@pytest.mark.asyncio
async def test_docker_registry_save(registry: DockerRegistryFixture):
    """Test saving and loading registry."""

    registry2: DockerRegistry = DockerRegistry(registry.file)
    port: Optional[int] = registry2.get_container_host_port(registry.container_id)
    assert port is not None, f"Container {registry.container_id} not found in registry"
    assert port == registry.port, f"Expected port {registry.port}, got {port}"

    hash: Optional[str] = registry2.get_container_config_hash(registry.container_id)
    assert hash is not None, f"Config hash for {registry.container_id} not found in registry"
    assert hash == "test-hash-123", f"Expected hash {registry.hash}, got {hash}"


@pytest.mark.asyncio
async def test_docker_registry_cleanup(registry: DockerRegistryFixture):
    registry2: DockerRegistry = DockerRegistry(registry.file)
    registry2.unregister_container(registry.container_id)

    port: Optional[int] = registry2.get_container_host_port(registry.container_id)
    assert port is None, f"Container {registry.container_id} should not be found in registry"

    hash: Optional[str] = registry2.get_container_config_hash(registry.container_id)
    assert hash is None, f"Config hash for {registry.container_id} should not be found in registry"

@pytest.mark.asyncio
@pytest.mark.skip(reason="Port 22 is not always in use")
async def test_docker_utils_port_in_use(docker_utils: DockerUtils):
    in_use: bool = docker_utils.is_port_in_use(22)  # SSH port is usually in use
    assert in_use, "Port 22 should be in use"

@pytest.mark.asyncio
async def test_docker_utils_get_next_available_port(docker_utils: DockerUtils):
    available_port: int = docker_utils.get_next_available_port(9000)
    assert available_port >= 9000, f"Expected port > 9000, got {available_port}"
    assert available_port <= 65535, f"Expected port < 65535, got {available_port}"

@pytest.mark.asyncio
async def test_docker_utils_generate_config_hash(docker_utils: DockerUtils):
    config_dict: dict[str, Any] = {"mode": "connect", "headless": True}
    config_hash: str = docker_utils.generate_config_hash(config_dict)
    assert config_hash, "Config hash should not be empty"
    assert config_hash == "2d35bd49af790a2ed296e7d70f807cc29bd2e57bad78fa75a9d1e47ce2e315c4", f"Unexpected hash: {config_hash}"

@pytest.mark.asyncio
@pytest.mark.skip(reason="start.sh is missing")
async def test_docker_build_connect_image(skipif_docker_unavailable, docker_utils: DockerUtils):
    connect_image: str = await docker_utils.ensure_docker_image_exists(None, "connect")
    assert connect_image, "Failed to build connect mode image"

@pytest.mark.asyncio
@pytest.mark.skip(reason="Docker build fails with: Unable to locate package google-chrome-stable")
async def test_docker_build_launch_image(skipif_docker_unavailable, docker_utils: DockerUtils):
    launch_image: str = await docker_utils.ensure_docker_image_exists(None, "launch")
    assert launch_image, "Failed to build launch mode image"

@pytest.mark.asyncio
@pytest.mark.skip(reason="Docker build fails with: Unable to locate package google-chrome-stable")
async def test_docker_create_container(skipif_docker_unavailable, docker_utils: DockerUtils):
    launch_image: str = await docker_utils.ensure_docker_image_exists(None, "launch")
    assert launch_image, "Failed to build launch mode image"

    container_id: Optional[str] = None
    try:
        container_id = await docker_utils.create_container(
            image_name=launch_image,
            host_port=0, # Random port
            container_name="crawl4ai-test-container"
        )
        assert container_id, "Failed to create test container"

        # Verify container is running
        running: bool = await docker_utils.is_container_running(container_id)
        assert running, "Container is not running"

        # Test commands in container
        returncode: int
        returncode, _, _ = await docker_utils.exec_in_container(
            container_id, ["ls", "-la", "/"]
        )
        assert returncode == 0, "Command execution failed"

        # Verify Chrome is installed in the container
        returncode, stdout, stderr = await docker_utils.exec_in_container(
            container_id, ["which", "google-chrome"]
        )
        assert returncode == 0, "Chrome not found"

        # Test Chrome version
        returncode, stdout, stderr = await docker_utils.exec_in_container(
            container_id, ["google-chrome", "--version"]
        )
        assert returncode == 0, "Failed to get Chrome version"
    finally:
        if container_id:
            await docker_utils.remove_container(container_id)

@pytest.mark.asyncio
async def test_docker_connect_mode(tmp_path: Path):
    """Test Docker browser in connect mode.

    This tests the basic functionality of creating a browser in Docker
    connect mode and using it for navigation.
    """
    manager: Optional[BrowserManager] = None
    try:
        # Create Docker configuration
        docker_config = DockerConfig(
            mode="connect",
            persistent=False,
            remove_on_exit=True,
            user_data_dir=str(tmp_path)
        )

        # Create browser configuration
        browser_config = BrowserConfig(
            browser_mode="docker",
            headless=True,
            docker_config=docker_config
        )

        # Create browser manager

        manager = BrowserManager(browser_config=browser_config)

        # Start the browser
        await manager.start()

        # Create crawler config
        crawler_config = CrawlerRunConfig(url="https://example.com")

        # Get a page
        page, context = await manager.get_page(crawler_config)
        assert page, "Failed to get page"

        # Navigate to a website
        response: Optional[Response] = await page.goto("https://example.com")
        assert response, "Failed to navigate to example.com"

        # Get page title
        title: str = await page.title()
        assert title, "Failed to get page title"
    finally:
        if manager:
            await manager.close()

@pytest.mark.asyncio
async def test_docker_launch_mode(tmp_path: Path):
    """Test Docker browser in launch mode.

    This tests launching a Chrome browser within a Docker container
    on demand with custom settings.
    """
    manager: Optional[BrowserManager] = None
    try:
        # Create Docker configuration
        docker_config = DockerConfig(
            mode="launch",
            persistent=False,
            remove_on_exit=True,
            user_data_dir=str(tmp_path),
        )

        # Create browser configuration
        browser_config: BrowserConfig = BrowserConfig(
            browser_mode="docker",
            headless=True,
            text_mode=True,  # Enable text mode for faster operation
            docker_config=docker_config
        )

        # Create browser manager
        manager = BrowserManager(browser_config=browser_config)

        # Start the browser
        await manager.start()

        # Create crawler config
        crawler_config: CrawlerRunConfig = CrawlerRunConfig(url="https://example.com")

        # Get a page
        page, context = await manager.get_page(crawler_config)
        assert page, "Failed to get page"

        # Navigate to a website
        response: Optional[Response] = await page.goto("https://example.com")
        assert response, "Failed to navigate to example.com"

        # Get page title
        title: str = await page.title()
        assert title, "Failed to get page title"
    finally:
        if manager:
            await manager.close()

@pytest.mark.asyncio
async def test_docker_persistent_storage(tmp_path: Path):
    """Test Docker browser with persistent storage.

    This tests creating localStorage data in one session and verifying
    it persists to another session when using persistent storage.
    """
    manager1: Optional[BrowserManager] = None
    manager2: Optional[BrowserManager] = None
    test_id = uuid.uuid4().hex[:8]
    try:
        # Create Docker configuration with persistence
        docker_config = DockerConfig(
            mode="connect",
            persistent=True,  # Keep container running between sessions
            user_data_dir=str(tmp_path),
            container_user_data_dir="/data"
        )

        # Create browser configuration
        browser_config = BrowserConfig(
            browser_mode="docker",
            headless=True,
            docker_config=docker_config
        )

        # Create first browser manager
        manager1 = BrowserManager(browser_config=browser_config)

        # Start the browser
        await manager1.start()

        # Create crawler config
        crawler_config: CrawlerRunConfig = CrawlerRunConfig()

        # Get a page
        page1, context1 = await manager1.get_page(crawler_config)
        assert page1, "Failed to get page"

        # Navigate to example.com
        response: Optional[Response] = await page1.goto("https://example.com")
        assert response, "Failed to navigate to example.com"

        # Set localStorage item
        test_value = f"test_value_{test_id}"
        await page1.evaluate(f"localStorage.setItem('test_key', '{test_value}')")

        # Close the first browser manager
        await manager1.close()

        # Create second browser manager with same config
        manager2 = BrowserManager(browser_config=browser_config)

        # Start the browser
        await manager2.start()

        # Get a page
        page2, context2 = await manager2.get_page(crawler_config)
        assert page2, "Failed to get page"

        # Navigate to same site
        await page2.goto("https://example.com")

        # Get localStorage item
        value = await page2.evaluate("localStorage.getItem('test_key')")

        # Check if persistence worked
        assert value == test_value, f"Storage persistence failed! Expected {test_value}, got {value}"
    finally:
        if manager1:
            await manager1.close()
        if manager2:
            await manager2.close()

@pytest.mark.asyncio
async def test_docker_parallel_pages():
    """Test Docker browser with parallel page creation.

    This tests the ability to create and use multiple pages in parallel
    from a single Docker browser instance.
    """
    manager: Optional[BrowserManager] = None
    try:
        # Create Docker configuration
        docker_config: DockerConfig = DockerConfig(
            mode="connect",
            persistent=False,
            remove_on_exit=True
        )

        # Create browser configuration
        browser_config: BrowserConfig = BrowserConfig(
            browser_mode="docker",
            headless=True,
            docker_config=docker_config
        )

        # Create browser manager
        manager = BrowserManager(browser_config=browser_config)

        # Start the browser
        await manager.start()

        # Create crawler config
        crawler_config = CrawlerRunConfig()

        # Get multiple pages
        page_count: int = 3
        pages = await manager.get_pages(crawler_config, count=page_count)

        assert len(pages) == page_count, f"Expected {page_count} pages, got {len(pages)}"

        # Navigate to different sites with each page
        tasks = []
        for i, (page, _) in enumerate(pages):
            tasks.append(page.goto(f"https://example.com?page={i}"))

        # Wait for all navigations to complete
        await asyncio.gather(*tasks)

        # Get titles from all pages
        for i, (page, _) in enumerate(pages):
            title: str = await page.title()
            assert title, f"Failed to get title for page {i}"
    finally:
        if manager:
            await manager.close()

@pytest.mark.asyncio
@pytest.mark.skip(reason="Docker container is not created")
async def test_docker_registry_reuse(registry: DockerRegistryFixture, docker_utils: DockerUtils):
    """Test Docker container reuse via registry.

    This tests that containers with matching configurations
    are reused rather than creating new ones.
    """
    manager1: Optional[BrowserManager] = None
    manager2: Optional[BrowserManager] = None
    container_id1: Optional[str] = None
    container_id2: Optional[str] = None
    try:
        # Create identical Docker configurations with custom registry
        docker_config1: DockerConfig = DockerConfig(
            mode="connect",
            persistent=True,  # Keep container running after closing
            registry_file=registry.file
        )

        # Create first browser configuration
        browser_config1: BrowserConfig = BrowserConfig(
            browser_mode="docker",
            headless=True,
            docker_config=docker_config1
        )

        # Create first browser manager
        manager1 = BrowserManager(browser_config=browser_config1)

        # Start the first browser
        await manager1.start()

        # Get container ID from the strategy
        docker_strategy1: BaseBrowserStrategy = manager1._strategy
        assert isinstance(docker_strategy1, DockerBrowserStrategy), f"Expected DockerBrowserStrategy got {type(docker_strategy1)}"
        container_id1 = docker_strategy1.container_id
        assert container_id1, "Failed to get container ID"

        # Close the first manager but keep container running
        await manager1.close()

        # Create second Docker configuration identical to first
        docker_config2 = DockerConfig(
            mode="connect",
            persistent=True,
            registry_file=registry.file
        )

        # Create second browser configuration
        browser_config2 = BrowserConfig(
            browser_mode="docker",
            headless=True,
            docker_config=docker_config2
        )

        # Create second browser manager
        manager2 = BrowserManager(browser_config=browser_config2)

        # Start the second browser - should reuse existing container
        await manager2.start()

        # Get container ID from the second strategy
        docker_strategy2: BaseBrowserStrategy = manager1._strategy
        assert isinstance(docker_strategy2, DockerBrowserStrategy), f"Expected DockerBrowserStrategy got {type(docker_strategy2)}"
        container_id2 = docker_strategy2.container_id
        assert container_id2, "Failed to get container ID"

        # Verify container reuse
        assert container_id1 == container_id2, "Container IDs do not match - expected reuse"
    finally:
        if manager1:
            await manager1.close()
        if manager2:
            await manager2.close()
        if container_id1:
            await docker_utils.remove_container(container_id1, force=True)
        if container_id2 and container_id1 != container_id2:
            await docker_utils.remove_container(container_id2, force=True)

if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
