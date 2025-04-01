# browser_hub_manager.py
import hashlib
import json
import asyncio
from typing import Dict, Optional
from .manager import BrowserManager, UnavailableBehavior
from ..async_configs import BrowserConfig
from ..async_logger import AsyncLogger

class BrowserHub:
    """
    Manages Browser-Hub instances for sharing across multiple pipelines.
    
    This class provides centralized management for browser resources, allowing
    multiple pipelines to share browser instances efficiently, connect to
    existing browser hubs, or create new ones with custom configurations.
    """
    _instances: Dict[str, BrowserManager] = {}
    _lock = asyncio.Lock()
    
    @classmethod
    async def get_or_create_hub(
        cls, 
        config: Optional[BrowserConfig] = None,
        hub_id: Optional[str] = None,
        connection_info: Optional[str] = None,
        logger: Optional[AsyncLogger] = None,
        max_browsers_per_config: int = 10,
        max_pages_per_browser: int = 5,
        initial_pool_size: int = 1,
        page_configs: Optional[list] = None
    ) -> BrowserManager:
        """
        Get an existing Browser-Hub or create a new one based on parameters.
        
        Args:
            config: Browser configuration for new hub
            hub_id: Identifier for the hub instance
            connection_info: Connection string for existing hub
            logger: Logger for recording events and errors
            max_browsers_per_config: Maximum browsers per configuration
            max_pages_per_browser: Maximum pages per browser
            initial_pool_size: Initial number of browsers to create
            page_configs: Optional configurations for pre-warming pages
            
        Returns:
            BrowserManager: The requested browser manager instance
        """
        async with cls._lock:
            # Scenario 3: Use existing hub via connection info
            if connection_info:
                instance_key = f"connection:{connection_info}"
                if instance_key not in cls._instances:
                    cls._instances[instance_key] = await cls._connect_to_browser_hub(
                        connection_info, logger
                    )
                return cls._instances[instance_key]
                
            # Scenario 2: Custom configured hub
            if config:
                config_hash = cls._hash_config(config)
                instance_key = hub_id or f"config:{config_hash}"
                if instance_key not in cls._instances:
                    cls._instances[instance_key] = await cls._create_browser_hub(
                        config, 
                        logger,
                        max_browsers_per_config,
                        max_pages_per_browser,
                        initial_pool_size,
                        page_configs
                    )
                return cls._instances[instance_key]
            
            # Scenario 1: Default hub
            instance_key = "default"
            if instance_key not in cls._instances:
                cls._instances[instance_key] = await cls._create_default_browser_hub(
                    logger,
                    max_browsers_per_config,
                    max_pages_per_browser,
                    initial_pool_size
                )
            return cls._instances[instance_key]
    
    @classmethod
    async def _create_browser_hub(
        cls, 
        config: BrowserConfig,
        logger: Optional[AsyncLogger],
        max_browsers_per_config: int,
        max_pages_per_browser: int,
        initial_pool_size: int,
        page_configs: Optional[list]
    ) -> BrowserManager:
        """Create a new browser hub with the specified configuration."""
        manager = BrowserManager(
            browser_config=config,
            logger=logger,
            unavailable_behavior=UnavailableBehavior.ON_DEMAND,
            max_browsers_per_config=max_browsers_per_config
        )
        
        # Initialize the pool
        await manager.initialize_pool(
            browser_configs=[config] if config else None,
            browsers_per_config=initial_pool_size,
            page_configs=page_configs
        )
        
        return manager
    
    @classmethod
    async def _create_default_browser_hub(
        cls,
        logger: Optional[AsyncLogger],
        max_browsers_per_config: int,
        max_pages_per_browser: int,
        initial_pool_size: int
    ) -> BrowserManager:
        """Create a default browser hub with standard settings."""
        config = BrowserConfig(headless=True)
        return await cls._create_browser_hub(
            config, 
            logger, 
            max_browsers_per_config, 
            max_pages_per_browser, 
            initial_pool_size,
            None
        )
    
    @classmethod
    async def _connect_to_browser_hub(
        cls, 
        connection_info: str,
        logger: Optional[AsyncLogger]
    ) -> BrowserManager:
        """
        Connect to an existing browser hub.
        
        Note: This is a placeholder for future remote connection functionality.
        Currently creates a local instance.
        """
        if logger:
            logger.info(
                message="Remote browser hub connections not yet implemented. Creating local instance.",
                tag="BROWSER_HUB"
            )
        # For now, create a default local instance
        return await cls._create_default_browser_hub(
            logger, 
            max_browsers_per_config=10, 
            max_pages_per_browser=5, 
            initial_pool_size=1
        )
    
    @classmethod
    def _hash_config(cls, config: BrowserConfig) -> str:
        """Create a hash of the browser configuration for identification."""
        # Convert config to dictionary, excluding any callable objects
        config_dict = config.__dict__.copy()
        for key in list(config_dict.keys()):
            if callable(config_dict[key]):
                del config_dict[key]
        
        # Convert to canonical JSON string
        config_json = json.dumps(config_dict, sort_keys=True, default=str)
        
        # Hash the JSON
        config_hash = hashlib.sha256(config_json.encode()).hexdigest()
        return config_hash
    
    @classmethod
    async def shutdown_all(cls):
        """Close all browser hub instances and clear the registry."""
        async with cls._lock:
            shutdown_tasks = []
            for hub in cls._instances.values():
                shutdown_tasks.append(hub.close())
            
            if shutdown_tasks:
                await asyncio.gather(*shutdown_tasks)
            
            cls._instances.clear()