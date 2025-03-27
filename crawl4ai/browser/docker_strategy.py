"""Docker browser strategy module for Crawl4AI.

This module provides browser strategies for running browsers in Docker containers,
which offers better isolation, consistency across platforms, and easy scaling.
"""

import os
import uuid
import asyncio
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path

from playwright.async_api import Page, BrowserContext

from ..async_logger import AsyncLogger
from ..async_configs import BrowserConfig, CrawlerRunConfig
from .docker_config import DockerConfig
from .docker_registry import DockerRegistry
from .docker_utils import DockerUtils
from .strategies import BuiltinBrowserStrategy


class DockerBrowserStrategy(BuiltinBrowserStrategy):
    """Docker-based browser strategy.
    
    Extends the BuiltinBrowserStrategy to run browsers in Docker containers.
    Supports two modes:
    1. "connect" - Uses a Docker image with Chrome already running
    2. "launch" - Starts Chrome within the container with custom settings
    
    Attributes:
        docker_config: Docker-specific configuration options
        container_id: ID of current Docker container
        container_name: Name assigned to the container
        registry: Registry for tracking and reusing containers
        docker_utils: Utilities for Docker operations
        chrome_process_id: Process ID of Chrome within container
        socat_process_id: Process ID of socat within container
        internal_cdp_port: Chrome's internal CDP port
        internal_mapped_port: Port that socat maps to internally
    """
    
    def __init__(self, config: BrowserConfig, logger: Optional[AsyncLogger] = None):
        """Initialize the Docker browser strategy.
        
        Args:
            config: Browser configuration including Docker-specific settings
            logger: Logger for recording events and errors
        """
        super().__init__(config, logger)
        
        # Initialize Docker-specific attributes
        self.docker_config = self.config.docker_config or DockerConfig()
        self.container_id = None
        self.container_name = f"crawl4ai-browser-{uuid.uuid4().hex[:8]}"
        self.registry = DockerRegistry(self.docker_config.registry_file)
        self.docker_utils = DockerUtils(logger)
        self.chrome_process_id = None
        self.socat_process_id = None
        self.internal_cdp_port = 9222  # Chrome's internal CDP port
        self.internal_mapped_port = 9223  # Port that socat maps to internally
        self.shutting_down = False
    
    async def _generate_config_hash(self) -> str:
        """Generate a hash of the configuration for container matching.
        
        Returns:
            Hash string uniquely identifying this configuration
        """
        # Create a dict with the relevant parts of the config
        config_dict = {
            "image": self.docker_config.image,
            "mode": self.docker_config.mode,
            "browser_type": self.config.browser_type,
            "headless": self.config.headless,
        }
        
        # Add browser-specific config if in launch mode
        if self.docker_config.mode == "launch":
            config_dict.update({
                "text_mode": self.config.text_mode,
                "light_mode": self.config.light_mode,
                "viewport_width": self.config.viewport_width,
                "viewport_height": self.config.viewport_height,
            })
        
        # Use the utility method to generate the hash
        return self.docker_utils.generate_config_hash(config_dict)
    
    async def _get_or_create_cdp_url(self) -> str:
        """Get CDP URL by either creating a new container or using an existing one.
        
        Returns:
            CDP URL for connecting to the browser
            
        Raises:
            Exception: If container creation or browser launch fails
        """
        # If CDP URL is explicitly provided, use it
        if self.config.cdp_url:
            return self.config.cdp_url
        
        # Ensure Docker image exists (will build if needed)
        image_name = await self.docker_utils.ensure_docker_image_exists(
            self.docker_config.image, 
            self.docker_config.mode
        )
        
        # Generate config hash for container matching
        config_hash = await self._generate_config_hash()
        
        # Look for existing container with matching config
        container_id = self.registry.find_container_by_config(config_hash, self.docker_utils)
        
        if container_id:
            # Use existing container
            self.container_id = container_id
            host_port = self.registry.get_container_host_port(container_id)
            if self.logger:
                self.logger.info(f"Using existing Docker container: {container_id[:12]}", tag="DOCKER")
        else:
            # Get a port for the new container
            host_port = self.docker_config.host_port or self.registry.get_next_available_port(self.docker_utils)
            
            # Prepare volumes list
            volumes = list(self.docker_config.volumes)
            
            # Add user data directory if specified
            if self.docker_config.user_data_dir:
                # Ensure user data directory exists
                os.makedirs(self.docker_config.user_data_dir, exist_ok=True)
                volumes.append(f"{self.docker_config.user_data_dir}:{self.docker_config.container_user_data_dir}")
                
                # Update config user_data_dir to point to container path
                self.config.user_data_dir = self.docker_config.container_user_data_dir
            
            # Create a new container
            container_id = await self.docker_utils.create_container(
                image_name=image_name,
                host_port=host_port,
                container_name=self.container_name,
                volumes=volumes,
                network=self.docker_config.network,
                env_vars=self.docker_config.env_vars,
                extra_args=self.docker_config.extra_args
            )
            
            if not container_id:
                raise Exception("Failed to create Docker container")
            
            self.container_id = container_id
            
            # Register the container
            self.registry.register_container(container_id, host_port, config_hash)
            
            # Wait for container to be ready
            await self.docker_utils.wait_for_container_ready(container_id)
            
            # Handle specific setup based on mode
            if self.docker_config.mode == "launch":
                # In launch mode, we need to start socat and Chrome
                await self.docker_utils.start_socat_in_container(container_id)
                
                # Build browser arguments
                browser_args = self._build_browser_args()
                
                # Launch Chrome
                await self.docker_utils.launch_chrome_in_container(container_id, browser_args)
                
                # Get PIDs for later cleanup
                self.chrome_process_id = await self.docker_utils.get_process_id_in_container(
                    container_id, "chrome"
                )
                self.socat_process_id = await self.docker_utils.get_process_id_in_container(
                    container_id, "socat"
                )
            
            # Wait for CDP to be ready
            await self.docker_utils.wait_for_cdp_ready(host_port)
            
            if self.logger:
                self.logger.success(f"Docker container ready: {container_id[:12]} on port {host_port}", tag="DOCKER")
        
        # Return CDP URL
        return f"http://localhost:{host_port}"
    
    def _build_browser_args(self) -> List[str]:
        """Build Chrome command line arguments based on BrowserConfig.
        
        Returns:
            List of command line arguments for Chrome
        """
        args = [
            "--no-sandbox",
            "--disable-gpu",
            f"--remote-debugging-port={self.internal_cdp_port}",
            "--remote-debugging-address=0.0.0.0",  # Allow external connections
            "--disable-dev-shm-usage",
        ]
        
        if self.config.headless:
            args.append("--headless=new")
            
        if self.config.viewport_width and self.config.viewport_height:
            args.append(f"--window-size={self.config.viewport_width},{self.config.viewport_height}")
            
        if self.config.user_agent:
            args.append(f"--user-agent={self.config.user_agent}")
            
        if self.config.text_mode:
            args.extend([
                "--blink-settings=imagesEnabled=false",
                "--disable-remote-fonts",
                "--disable-images",
                "--disable-javascript",
            ])
            
        if self.config.light_mode:
            # Import here to avoid circular import
            from .utils import get_browser_disable_options
            args.extend(get_browser_disable_options())
            
        if self.config.user_data_dir:
            args.append(f"--user-data-dir={self.config.user_data_dir}")
            
        if self.config.extra_args:
            args.extend(self.config.extra_args)
            
        return args
    
    async def close(self):
        """Close the browser and clean up Docker container if needed."""
        # Set shutting_down flag to prevent race conditions
        self.shutting_down = True
        
        # Store state if needed before closing
        if self.browser and self.docker_config.user_data_dir and self.docker_config.persistent:
            for context in self.browser.contexts:
                try:
                    storage_path = os.path.join(self.docker_config.user_data_dir, "storage_state.json")
                    await context.storage_state(path=storage_path)
                    if self.logger:
                        self.logger.debug("Persisted storage state before closing browser", tag="DOCKER")
                except Exception as e:
                    if self.logger:
                        self.logger.warning(
                            message="Failed to persist storage state: {error}",
                            tag="DOCKER",
                            params={"error": str(e)}
                        )
        
        # Close browser connection (but not container)
        if self.browser:
            await self.browser.close()
            self.browser = None
        
        # Only clean up container if not persistent
        if self.container_id and not self.docker_config.persistent:
            # Stop Chrome process in "launch" mode
            if self.docker_config.mode == "launch" and self.chrome_process_id:
                await self.docker_utils.stop_process_in_container(
                    self.container_id, self.chrome_process_id
                )
            
            # Stop socat process in "launch" mode
            if self.docker_config.mode == "launch" and self.socat_process_id:
                await self.docker_utils.stop_process_in_container(
                    self.container_id, self.socat_process_id
                )
            
            # Remove or stop container based on configuration
            if self.docker_config.remove_on_exit:
                await self.docker_utils.remove_container(self.container_id)
                # Unregister from registry
                self.registry.unregister_container(self.container_id)
            else:
                await self.docker_utils.stop_container(self.container_id)
            
            self.container_id = None
        
        # Close Playwright
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        
        self.shutting_down = False