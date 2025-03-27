"""Docker registry module for Crawl4AI.

This module provides a registry system for tracking and reusing Docker containers
across browser sessions, improving performance and resource utilization.
"""

import os
import json
import time
from typing import Dict, Optional

from ..utils import get_home_folder


class DockerRegistry:
    """Manages a registry of Docker containers used for browser automation.
    
    This registry tracks containers by configuration hash, allowing reuse of appropriately
    configured containers instead of creating new ones for each session.
    
    Attributes:
        registry_file (str): Path to the registry file
        containers (dict): Dictionary of container information
        port_map (dict): Map of host ports to container IDs
        last_port (int): Last port assigned
    """
    
    def __init__(self, registry_file: Optional[str] = None):
        """Initialize the registry with an optional path to the registry file.
        
        Args:
            registry_file: Path to the registry file. If None, uses default path.
        """
        # Use the same file path as BuiltinBrowserStrategy by default
        self.registry_file = registry_file or os.path.join(get_home_folder(), "builtin-browser", "browser_config.json")
        self.containers = {}  # Still maintain this for backward compatibility
        self.port_map = {}    # Will be populated from the shared file
        self.last_port = 9222
        self.load()
    
    def load(self):
        """Load container registry from file."""
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r') as f:
                    registry_data = json.load(f)
                    
                    # Initialize port_map if not present
                    if "port_map" not in registry_data:
                        registry_data["port_map"] = {}
                    
                    self.port_map = registry_data.get("port_map", {})
                    
                    # Extract container information from port_map entries of type "docker"
                    self.containers = {}
                    for port_str, browser_info in self.port_map.items():
                        if browser_info.get("browser_type") == "docker" and "container_id" in browser_info:
                            container_id = browser_info["container_id"]
                            self.containers[container_id] = {
                                "host_port": int(port_str),
                                "config_hash": browser_info.get("config_hash", ""),
                                "created_at": browser_info.get("created_at", time.time())
                            }
                    
                    # Get last port if available
                    if "last_port" in registry_data:
                        self.last_port = registry_data["last_port"]
                    else:
                        # Find highest port in port_map
                        ports = [int(p) for p in self.port_map.keys() if p.isdigit()]
                        self.last_port = max(ports + [9222])
                    
            except Exception as e:
                # Reset to defaults on error
                print(f"Error loading registry: {e}")
                self.containers = {}
                self.port_map = {}
                self.last_port = 9222
        else:
            # Initialize with defaults if file doesn't exist
            self.containers = {}
            self.port_map = {}
            self.last_port = 9222
    
    def save(self):
        """Save container registry to file."""
        # First load the current file to avoid overwriting other browser types
        current_data = {"port_map": {}, "last_port": self.last_port}
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r') as f:
                    current_data = json.load(f)
            except Exception:
                pass
        
        # Create a new port_map dictionary
        updated_port_map = {}
        
        # First, copy all non-docker entries from the existing port_map
        for port_str, browser_info in current_data.get("port_map", {}).items():
            if browser_info.get("browser_type") != "docker":
                updated_port_map[port_str] = browser_info
        
        # Then add all current docker container entries
        for container_id, container_info in self.containers.items():
            port_str = str(container_info["host_port"])
            updated_port_map[port_str] = {
                "browser_type": "docker",
                "container_id": container_id,
                "cdp_url": f"http://localhost:{port_str}",
                "config_hash": container_info["config_hash"],
                "created_at": container_info["created_at"]
            }
        
        # Replace the port_map with our updated version
        current_data["port_map"] = updated_port_map
        
        # Update last_port
        current_data["last_port"] = self.last_port
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)
        
        # Save the updated data
        with open(self.registry_file, 'w') as f:
            json.dump(current_data, f, indent=2)
    
    def register_container(self, container_id: str, host_port: int, config_hash: str, cdp_json_config: Optional[str] = None):
        """Register a container with its configuration hash and port mapping.
        
        Args:
            container_id: Docker container ID
            host_port: Host port mapped to container
            config_hash: Hash of configuration used to create container
            cdp_json_config: CDP JSON configuration if available
        """
        self.containers[container_id] = {
            "host_port": host_port,
            "config_hash": config_hash,
            "created_at": time.time()
        }
        
        # Update port_map to maintain compatibility with BuiltinBrowserStrategy
        port_str = str(host_port)
        self.port_map[port_str] = {
            "browser_type": "docker",
            "container_id": container_id,
            "cdp_url": f"http://localhost:{port_str}",
            "config_hash": config_hash,
            "created_at": time.time()
        }
        
        if cdp_json_config:
            self.port_map[port_str]["cdp_json_config"] = cdp_json_config
        
        self.save()
    
    def unregister_container(self, container_id: str):
        """Unregister a container.
        
        Args:
            container_id: Docker container ID to unregister
        """
        if container_id in self.containers:
            host_port = self.containers[container_id]["host_port"]
            port_str = str(host_port)
            
            # Remove from port_map
            if port_str in self.port_map:
                del self.port_map[port_str]
                
            # Remove from containers
            del self.containers[container_id]
            
            self.save()
    
    async def find_container_by_config(self, config_hash: str, docker_utils) -> Optional[str]:
        """Find a container that matches the given configuration hash.
        
        Args:
            config_hash: Hash of configuration to match
            docker_utils: DockerUtils instance to check running containers
            
        Returns:
            Container ID if found, None otherwise
        """
        # Search through port_map for entries with matching config_hash
        for port_str, browser_info in self.port_map.items():
            if (browser_info.get("browser_type") == "docker" and 
                browser_info.get("config_hash") == config_hash and 
                "container_id" in browser_info):
                
                container_id = browser_info["container_id"]
                if await docker_utils.is_container_running(container_id):
                    return container_id
        
        return None
    
    def get_container_host_port(self, container_id: str) -> Optional[int]:
        """Get the host port mapped to the container.
        
        Args:
            container_id: Docker container ID
            
        Returns:
            Host port if container is registered, None otherwise
        """
        if container_id in self.containers:
            return self.containers[container_id]["host_port"]
        return None
    
    def get_next_available_port(self, docker_utils) -> int:
        """Get the next available host port for Docker mapping.
        
        Args:
            docker_utils: DockerUtils instance to check port availability
            
        Returns:
            Available port number
        """
        # Start from last port + 1
        port = self.last_port + 1
        
        # Check if port is in use (either in our registry or system-wide)
        while str(port) in self.port_map or docker_utils.is_port_in_use(port):
            port += 1
        
        # Update last port
        self.last_port = port
        self.save()
        
        return port
    
    def get_container_config_hash(self, container_id: str) -> Optional[str]:
        """Get the configuration hash for a container.
        
        Args:
            container_id: Docker container ID
            
        Returns:
            Configuration hash if container is registered, None otherwise
        """
        if container_id in self.containers:
            return self.containers[container_id]["config_hash"]
        return None
    
    def cleanup_stale_containers(self, docker_utils):
        """Clean up containers that are no longer running.
        
        Args:
            docker_utils: DockerUtils instance to check container status
        """
        to_remove = []
        
        # Find containers that are no longer running
        for port_str, browser_info in self.port_map.items():
            if browser_info.get("browser_type") == "docker" and "container_id" in browser_info:
                container_id = browser_info["container_id"]
                if not docker_utils.is_container_running(container_id):
                    to_remove.append(container_id)
        
        # Remove stale containers
        for container_id in to_remove:
            self.unregister_container(container_id)