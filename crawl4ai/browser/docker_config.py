"""Docker configuration module for Crawl4AI browser automation.

This module provides configuration classes for Docker-based browser automation,
allowing flexible configuration of Docker containers for browsing.
"""

from typing import Dict, List, Optional, Union


class DockerConfig:
    """Configuration for Docker-based browser automation.
    
    This class contains Docker-specific settings to avoid cluttering BrowserConfig.
    
    Attributes:
        mode (str): Docker operation mode - "connect" or "launch".
            - "connect": Uses a container with Chrome already running
            - "launch": Dynamically configures and starts Chrome in container
        image (str): Docker image to use. If None, defaults from DockerUtils are used.
        registry_file (str): Path to container registry file for persistence.
        persistent (bool): Keep container running after browser closes.
        remove_on_exit (bool): Remove container on exit when not persistent.
        network (str): Docker network to use.
        volumes (List[str]): Volume mappings (e.g., ["host_path:container_path"]).
        env_vars (Dict[str, str]): Environment variables to set in container.
        extra_args (List[str]): Additional docker run arguments.
        host_port (int): Host port to map to container's 9223 port.
        user_data_dir (str): Path to user data directory on host.
        container_user_data_dir (str): Path to user data directory in container.
    """
    
    def __init__(
        self,
        mode: str = "connect",                     # "connect" or "launch" 
        image: Optional[str] = None,               # Docker image to use
        registry_file: Optional[str] = None,       # Path to registry file
        persistent: bool = False,                  # Keep container running after browser closes
        remove_on_exit: bool = True,               # Remove container on exit when not persistent
        network: Optional[str] = None,             # Docker network to use
        volumes: List[str] = None,                 # Volume mappings
        env_vars: Dict[str, str] = None,           # Environment variables
        extra_args: List[str] = None,              # Additional docker run arguments
        host_port: Optional[int] = None,           # Host port to map to container's 9223
        user_data_dir: Optional[str] = None,       # Path to user data directory on host
        container_user_data_dir: str = "/data",    # Path to user data directory in container
    ):
        """Initialize Docker configuration.
        
        Args:
            mode: Docker operation mode ("connect" or "launch")
            image: Docker image to use
            registry_file: Path to container registry file
            persistent: Whether to keep container running after browser closes
            remove_on_exit: Whether to remove container on exit when not persistent
            network: Docker network to use
            volumes: Volume mappings as list of strings
            env_vars: Environment variables as dictionary
            extra_args: Additional docker run arguments
            host_port: Host port to map to container's 9223
            user_data_dir: Path to user data directory on host
            container_user_data_dir: Path to user data directory in container
        """
        self.mode = mode
        self.image = image  # If None, defaults will be used from DockerUtils
        self.registry_file = registry_file
        self.persistent = persistent
        self.remove_on_exit = remove_on_exit
        self.network = network
        self.volumes = volumes or []
        self.env_vars = env_vars or {}
        self.extra_args = extra_args or []
        self.host_port = host_port
        self.user_data_dir = user_data_dir
        self.container_user_data_dir = container_user_data_dir
    
    def to_dict(self) -> Dict:
        """Convert this configuration to a dictionary.
        
        Returns:
            Dictionary representation of this configuration
        """
        return {
            "mode": self.mode,
            "image": self.image,
            "registry_file": self.registry_file,
            "persistent": self.persistent,
            "remove_on_exit": self.remove_on_exit,
            "network": self.network,
            "volumes": self.volumes,
            "env_vars": self.env_vars,
            "extra_args": self.extra_args,
            "host_port": self.host_port,
            "user_data_dir": self.user_data_dir,
            "container_user_data_dir": self.container_user_data_dir
        }
        
    @staticmethod
    def from_kwargs(kwargs: Dict) -> "DockerConfig":
        """Create a DockerConfig from a dictionary of keyword arguments.
        
        Args:
            kwargs: Dictionary of configuration options
            
        Returns:
            New DockerConfig instance
        """
        return DockerConfig(
            mode=kwargs.get("mode", "connect"),
            image=kwargs.get("image"),
            registry_file=kwargs.get("registry_file"),
            persistent=kwargs.get("persistent", False),
            remove_on_exit=kwargs.get("remove_on_exit", True),
            network=kwargs.get("network"),
            volumes=kwargs.get("volumes"),
            env_vars=kwargs.get("env_vars"),
            extra_args=kwargs.get("extra_args"),
            host_port=kwargs.get("host_port"),
            user_data_dir=kwargs.get("user_data_dir"),
            container_user_data_dir=kwargs.get("container_user_data_dir", "/data")
        )
        
    def clone(self, **kwargs) -> "DockerConfig":
        """Create a copy of this configuration with updated values.
        
        Args:
            **kwargs: Key-value pairs of configuration options to update
            
        Returns:
            DockerConfig: A new instance with the specified updates
        """
        config_dict = self.to_dict()
        config_dict.update(kwargs)
        return DockerConfig.from_kwargs(config_dict)