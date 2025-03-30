"""Test examples for Docker Browser Strategy.

These examples demonstrate the functionality of Docker Browser Strategy
and serve as functional tests.
"""

import asyncio
import os
import sys
import shutil
import uuid

# Add the project root to Python path if running directly
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from crawl4ai.browser import BrowserManager
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_logger import AsyncLogger
from crawl4ai.browser import DockerConfig
from crawl4ai.browser import DockerRegistry
from crawl4ai.browser import DockerUtils

# Create a logger for clear terminal output
logger = AsyncLogger(verbose=True, log_file=None)

# Global Docker utils instance
docker_utils = DockerUtils(logger)

async def test_docker_components():
    """Test Docker utilities, registry, and image building.
    
    This function tests the core Docker components before running the browser tests.
    It validates DockerRegistry, DockerUtils, and builds test images to ensure
    everything is functioning correctly.
    """
    logger.info("Testing Docker components", tag="SETUP")
    
    # Create a test registry directory
    registry_dir = os.path.join(os.path.dirname(__file__), "test_registry")
    registry_file = os.path.join(registry_dir, "test_registry.json")
    os.makedirs(registry_dir, exist_ok=True)
    
    try:
        # 1. Test DockerRegistry
        logger.info("Testing DockerRegistry...", tag="SETUP")
        registry = DockerRegistry(registry_file)
        
        # Test saving and loading registry
        test_container_id = "test-container-123"
        registry.register_container(test_container_id, 9876, "test-hash-123")
        registry.save()
        
        # Create a new registry instance that loads from the file
        registry2 = DockerRegistry(registry_file)
        port = registry2.get_container_host_port(test_container_id)
        hash_value = registry2.get_container_config_hash(test_container_id)
        
        if port != 9876 or hash_value != "test-hash-123":
            logger.error("DockerRegistry persistence failed", tag="SETUP")
            return False
            
        # Clean up test container from registry
        registry2.unregister_container(test_container_id)
        logger.success("DockerRegistry works correctly", tag="SETUP")
        
        # 2. Test DockerUtils
        logger.info("Testing DockerUtils...", tag="SETUP")
        
        # Test port detection
        in_use = docker_utils.is_port_in_use(22)  # SSH port is usually in use
        logger.info(f"Port 22 in use: {in_use}", tag="SETUP")
        
        # Get next available port
        available_port = docker_utils.get_next_available_port(9000)
        logger.info(f"Next available port: {available_port}", tag="SETUP")
        
        # Test config hash generation
        config_dict = {"mode": "connect", "headless": True}
        config_hash = docker_utils.generate_config_hash(config_dict)
        logger.info(f"Generated config hash: {config_hash[:8]}...", tag="SETUP")
        
        # 3. Test Docker is available
        logger.info("Checking Docker availability...", tag="SETUP")
        if not await check_docker_available():
            logger.error("Docker is not available - cannot continue tests", tag="SETUP")
            return False
            
        # 4. Test building connect image
        logger.info("Building connect mode Docker image...", tag="SETUP")
        connect_image = await docker_utils.ensure_docker_image_exists(None, "connect")
        if not connect_image:
            logger.error("Failed to build connect mode image", tag="SETUP")
            return False
        logger.success(f"Successfully built connect image: {connect_image}", tag="SETUP")
        
        # 5. Test building launch image
        logger.info("Building launch mode Docker image...", tag="SETUP")
        launch_image = await docker_utils.ensure_docker_image_exists(None, "launch")
        if not launch_image:
            logger.error("Failed to build launch mode image", tag="SETUP")
            return False
        logger.success(f"Successfully built launch image: {launch_image}", tag="SETUP")
        
        # 6. Test creating and removing container
        logger.info("Testing container creation and removal...", tag="SETUP")
        container_id = await docker_utils.create_container(
            image_name=launch_image,
            host_port=available_port,
            container_name="crawl4ai-test-container"
        )
        
        if not container_id:
            logger.error("Failed to create test container", tag="SETUP")
            return False
            
        logger.info(f"Created test container: {container_id[:12]}", tag="SETUP")
        
        # Verify container is running
        running = await docker_utils.is_container_running(container_id)
        if not running:
            logger.error("Test container is not running", tag="SETUP")
            await docker_utils.remove_container(container_id)
            return False
            
        # Test commands in container
        logger.info("Testing command execution in container...", tag="SETUP")
        returncode, stdout, stderr = await docker_utils.exec_in_container(
            container_id, ["ls", "-la", "/"]
        )
        
        if returncode != 0:
            logger.error(f"Command execution failed: {stderr}", tag="SETUP")
            await docker_utils.remove_container(container_id)
            return False
            
        # Verify Chrome is installed in the container
        returncode, stdout, stderr = await docker_utils.exec_in_container(
            container_id, ["which", "chromium"]
        )
        
        if returncode != 0:
            logger.error("Chrome not found in container", tag="SETUP")
            await docker_utils.remove_container(container_id)
            return False
            
        chrome_path = stdout.strip()
        logger.info(f"Chrome found at: {chrome_path}", tag="SETUP")
        
        # Test Chrome version
        returncode, stdout, stderr = await docker_utils.exec_in_container(
            container_id, ["chromium", "--version"]
        )
        
        if returncode != 0:
            logger.error(f"Failed to get Chrome version: {stderr}", tag="SETUP")
            await docker_utils.remove_container(container_id)
            return False
            
        logger.info(f"Chrome version: {stdout.strip()}", tag="SETUP")
        
        # Remove test container
        removed = await docker_utils.remove_container(container_id)
        if not removed:
            logger.error("Failed to remove test container", tag="SETUP")
            return False
            
        logger.success("Test container removed successfully", tag="SETUP")
        
        # All components tested successfully
        logger.success("All Docker components tested successfully", tag="SETUP")
        return True
        
    except Exception as e:
        logger.error(f"Docker component tests failed: {str(e)}", tag="SETUP")
        return False
    finally:
        # Clean up registry test directory
        if os.path.exists(registry_dir):
            shutil.rmtree(registry_dir)

async def test_docker_connect_mode():
    """Test Docker browser in connect mode.
    
    This tests the basic functionality of creating a browser in Docker
    connect mode and using it for navigation.
    """
    logger.info("Testing Docker browser in connect mode", tag="TEST")
    
    # Create temp directory for user data
    temp_dir = os.path.join(os.path.dirname(__file__), "tmp_user_data")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Create Docker configuration
        docker_config = DockerConfig(
            mode="connect",
            persistent=False,
            remove_on_exit=True,
            user_data_dir=temp_dir
        )
        
        # Create browser configuration
        browser_config = BrowserConfig(
            browser_mode="docker",
            headless=True,
            docker_config=docker_config
        )
        
        # Create browser manager
        manager = BrowserManager(browser_config=browser_config, logger=logger)
        
        # Start the browser
        await manager.start()
        logger.info("Browser started successfully", tag="TEST")
        
        # Create crawler config
        crawler_config = CrawlerRunConfig(url="https://example.com")
        
        # Get a page
        page, context = await manager.get_page(crawler_config)
        logger.info("Got page successfully", tag="TEST")
        
        # Navigate to a website
        await page.goto("https://example.com")
        logger.info("Navigated to example.com", tag="TEST")
        
        # Get page title
        title = await page.title()
        logger.info(f"Page title: {title}", tag="TEST")
        
        # Clean up
        await manager.close()
        logger.info("Browser closed successfully", tag="TEST")
        
        return True
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        # Ensure cleanup
        try:
            await manager.close()
        except:
            pass
        return False
    finally:
        # Clean up the temp directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

async def test_docker_launch_mode():
    """Test Docker browser in launch mode.
    
    This tests launching a Chrome browser within a Docker container
    on demand with custom settings.
    """
    logger.info("Testing Docker browser in launch mode", tag="TEST")
    
    # Create temp directory for user data
    temp_dir = os.path.join(os.path.dirname(__file__), "tmp_user_data_launch")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Create Docker configuration
        docker_config = DockerConfig(
            mode="launch",
            persistent=False,
            remove_on_exit=True,
            user_data_dir=temp_dir
        )
        
        # Create browser configuration
        browser_config = BrowserConfig(
            browser_mode="docker",
            headless=True,
            text_mode=True,  # Enable text mode for faster operation
            docker_config=docker_config
        )
        
        # Create browser manager
        manager = BrowserManager(browser_config=browser_config, logger=logger)
        
        # Start the browser
        await manager.start()
        logger.info("Browser started successfully", tag="TEST")
        
        # Create crawler config
        crawler_config = CrawlerRunConfig(url="https://example.com")
        
        # Get a page
        page, context = await manager.get_page(crawler_config)
        logger.info("Got page successfully", tag="TEST")
        
        # Navigate to a website
        await page.goto("https://example.com")
        logger.info("Navigated to example.com", tag="TEST")
        
        # Get page title
        title = await page.title()
        logger.info(f"Page title: {title}", tag="TEST")
        
        # Clean up
        await manager.close()
        logger.info("Browser closed successfully", tag="TEST")
        
        return True
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        # Ensure cleanup
        try:
            await manager.close()
        except:
            pass
        return False
    finally:
        # Clean up the temp directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

async def test_docker_persistent_storage():
    """Test Docker browser with persistent storage.
    
    This tests creating localStorage data in one session and verifying
    it persists to another session when using persistent storage.
    """
    logger.info("Testing Docker browser with persistent storage", tag="TEST")
    
    # Create a unique temp directory
    test_id = uuid.uuid4().hex[:8]
    temp_dir = os.path.join(os.path.dirname(__file__), f"tmp_user_data_persist_{test_id}")
    os.makedirs(temp_dir, exist_ok=True)
    
    manager1 = None
    manager2 = None
    
    try:
        # Create Docker configuration with persistence
        docker_config = DockerConfig(
            mode="connect",
            persistent=True,  # Keep container running between sessions
            user_data_dir=temp_dir,
            container_user_data_dir="/data"
        )
        
        # Create browser configuration
        browser_config = BrowserConfig(
            browser_mode="docker",
            headless=True,
            docker_config=docker_config
        )
        
        # Create first browser manager
        manager1 = BrowserManager(browser_config=browser_config, logger=logger)
        
        # Start the browser
        await manager1.start()
        logger.info("First browser started successfully", tag="TEST")
        
        # Create crawler config
        crawler_config = CrawlerRunConfig()
        
        # Get a page
        page1, context1 = await manager1.get_page(crawler_config)
        
        # Navigate to example.com
        await page1.goto("https://example.com")
        
        # Set localStorage item
        test_value = f"test_value_{test_id}"
        await page1.evaluate(f"localStorage.setItem('test_key', '{test_value}')")
        logger.info(f"Set localStorage test_key = {test_value}", tag="TEST")
        
        # Close the first browser manager
        await manager1.close()
        logger.info("First browser closed", tag="TEST")
        
        # Create second browser manager with same config
        manager2 = BrowserManager(browser_config=browser_config, logger=logger)
        
        # Start the browser
        await manager2.start()
        logger.info("Second browser started successfully", tag="TEST")
        
        # Get a page
        page2, context2 = await manager2.get_page(crawler_config)
        
        # Navigate to same site
        await page2.goto("https://example.com")
        
        # Get localStorage item
        value = await page2.evaluate("localStorage.getItem('test_key')")
        logger.info(f"Retrieved localStorage test_key = {value}", tag="TEST")
        
        # Check if persistence worked
        if value == test_value:
            logger.success("Storage persistence verified!", tag="TEST")
        else:
            logger.error(f"Storage persistence failed! Expected {test_value}, got {value}", tag="TEST")
        
        # Clean up
        await manager2.close()
        logger.info("Second browser closed successfully", tag="TEST")
        
        return value == test_value
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        # Ensure cleanup
        try:
            if manager1:
                await manager1.close()
            if manager2:
                await manager2.close()
        except:
            pass
        return False
    finally:
        # Clean up the temp directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

async def test_docker_parallel_pages():
    """Test Docker browser with parallel page creation.
    
    This tests the ability to create and use multiple pages in parallel
    from a single Docker browser instance.
    """
    logger.info("Testing Docker browser with parallel pages", tag="TEST")
    
    try:
        # Create Docker configuration
        docker_config = DockerConfig(
            mode="connect",
            persistent=False,
            remove_on_exit=True
        )
        
        # Create browser configuration
        browser_config = BrowserConfig(
            browser_mode="docker",
            headless=True,
            docker_config=docker_config
        )
        
        # Create browser manager
        manager = BrowserManager(browser_config=browser_config, logger=logger)
        
        # Start the browser
        await manager.start()
        logger.info("Browser started successfully", tag="TEST")
        
        # Create crawler config
        crawler_config = CrawlerRunConfig()
        
        # Get multiple pages
        page_count = 3
        pages = await manager.get_pages(crawler_config, count=page_count)
        logger.info(f"Got {len(pages)} pages successfully", tag="TEST")
        
        if len(pages) != page_count:
            logger.error(f"Expected {page_count} pages, got {len(pages)}", tag="TEST")
            await manager.close()
            return False
            
        # Navigate to different sites with each page
        tasks = []
        for i, (page, _) in enumerate(pages):
            tasks.append(page.goto(f"https://example.com?page={i}"))
            
        # Wait for all navigations to complete
        await asyncio.gather(*tasks)
        logger.info("All pages navigated successfully", tag="TEST")
        
        # Get titles from all pages
        titles = []
        for i, (page, _) in enumerate(pages):
            title = await page.title()
            titles.append(title)
            logger.info(f"Page {i+1} title: {title}", tag="TEST")
        
        # Clean up
        await manager.close()
        logger.info("Browser closed successfully", tag="TEST")
        
        return True
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        # Ensure cleanup
        try:
            await manager.close()
        except:
            pass
        return False

async def test_docker_registry_reuse():
    """Test Docker container reuse via registry.
    
    This tests that containers with matching configurations
    are reused rather than creating new ones.
    """
    logger.info("Testing Docker container reuse via registry", tag="TEST")
    
    # Create registry for this test
    registry_dir = os.path.join(os.path.dirname(__file__), "registry_reuse_test")
    registry_file = os.path.join(registry_dir, "registry.json")
    os.makedirs(registry_dir, exist_ok=True)
    
    manager1 = None
    manager2 = None
    container_id1 = None
    
    try:
        # Create identical Docker configurations with custom registry
        docker_config1 = DockerConfig(
            mode="connect",
            persistent=True,  # Keep container running after closing
            registry_file=registry_file
        )
        
        # Create first browser configuration
        browser_config1 = BrowserConfig(
            browser_mode="docker",
            headless=True,
            docker_config=docker_config1
        )
        
        # Create first browser manager
        manager1 = BrowserManager(browser_config=browser_config1, logger=logger)
        
        # Start the first browser
        await manager1.start()
        logger.info("First browser started successfully", tag="TEST")
        
        # Get container ID from the strategy
        docker_strategy1 = manager1.strategy
        container_id1 = docker_strategy1.container_id
        logger.info(f"First browser container ID: {container_id1[:12]}", tag="TEST")
        
        # Close the first manager but keep container running
        await manager1.close()
        logger.info("First browser closed", tag="TEST")
        
        # Create second Docker configuration identical to first
        docker_config2 = DockerConfig(
            mode="connect",
            persistent=True,
            registry_file=registry_file
        )
        
        # Create second browser configuration
        browser_config2 = BrowserConfig(
            browser_mode="docker",
            headless=True,
            docker_config=docker_config2
        )
        
        # Create second browser manager
        manager2 = BrowserManager(browser_config=browser_config2, logger=logger)
        
        # Start the second browser - should reuse existing container
        await manager2.start()
        logger.info("Second browser started successfully", tag="TEST")
        
        # Get container ID from the second strategy
        docker_strategy2 = manager2.strategy
        container_id2 = docker_strategy2.container_id
        logger.info(f"Second browser container ID: {container_id2[:12]}", tag="TEST")
        
        # Verify container reuse
        if container_id1 == container_id2:
            logger.success("Container reuse successful - using same container!", tag="TEST")
        else:
            logger.error("Container reuse failed - new container created!", tag="TEST")
        
        # Clean up
        docker_strategy2.docker_config.persistent = False
        docker_strategy2.docker_config.remove_on_exit = True
        await manager2.close()
        logger.info("Second browser closed and container removed", tag="TEST")
        
        return container_id1 == container_id2
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        # Ensure cleanup
        try:
            if manager1:
                await manager1.close()
            if manager2:
                await manager2.close()
            # Make sure container is removed
            if container_id1:
                await docker_utils.remove_container(container_id1, force=True)
        except:
            pass
        return False
    finally:
        # Clean up registry directory
        if os.path.exists(registry_dir):
            shutil.rmtree(registry_dir)

async def run_tests():
    """Run all tests sequentially."""
    results = []
    
    logger.info("Starting Docker Browser Strategy tests", tag="TEST")
    
    # Check if Docker is available
    if not await check_docker_available():
        logger.error("Docker is not available - skipping tests", tag="TEST")
        return
    
    # First test Docker components
    # setup_result = await test_docker_components()
    # if not setup_result:
    #     logger.error("Docker component tests failed - skipping browser tests", tag="TEST")
    #     return
    
    # Run browser tests
    results.append(await test_docker_connect_mode())
    results.append(await test_docker_launch_mode())
    results.append(await test_docker_persistent_storage())
    results.append(await test_docker_parallel_pages())
    results.append(await test_docker_registry_reuse())
    
    # Print summary
    total = len(results)
    passed = sum(1 for r in results if r)
    logger.info(f"Tests complete: {passed}/{total} passed", tag="SUMMARY")
    
    if passed == total:
        logger.success("All tests passed!", tag="SUMMARY")
    else:
        logger.error(f"{total - passed} tests failed", tag="SUMMARY")

async def check_docker_available() -> bool:
    """Check if Docker is available on the system.
    
    Returns:
        bool: True if Docker is available, False otherwise
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        return proc.returncode == 0 and stdout
    except:
        return False

if __name__ == "__main__":
    asyncio.run(run_tests())