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
        self.registry_file = registry_file or os.path.join(get_home_folder(), "docker_browser_registry.json")
        self.containers = {}
        self.port_map = {}
        self.last_port = 9222
        self.load()
    
    def load(self):
        """Load container registry from file."""
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r') as f:
                    registry_data = json.load(f)
                    self.containers = registry_data.get("containers", {})
                    self.port_map = registry_data.get("ports", {})
                    self.last_port = registry_data.get("last_port", 9222)
            except Exception:
                # Reset to defaults on error
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
        os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)
        with open(self.registry_file, 'w') as f:
            json.dump({
                "containers": self.containers,
                "ports": self.port_map,
                "last_port": self.last_port
            }, f, indent=2)
    
    def register_container(self, container_id: str, host_port: int, config_hash: str):
        """Register a container with its configuration hash and port mapping.
        
        Args:
            container_id: Docker container ID
            host_port: Host port mapped to container
            config_hash: Hash of configuration used to create container
        """
        self.containers[container_id] = {
            "host_port": host_port,
            "config_hash": config_hash,
            "created_at": time.time()
        }
        self.port_map[str(host_port)] = container_id
        self.save()
    
    def unregister_container(self, container_id: str):
        """Unregister a container.
        
        Args:
            container_id: Docker container ID to unregister
        """
        if container_id in self.containers:
            host_port = self.containers[container_id]["host_port"]
            if str(host_port) in self.port_map:
                del self.port_map[str(host_port)]
            del self.containers[container_id]
            self.save()
    
    def find_container_by_config(self, config_hash: str, docker_utils) -> Optional[str]:
        """Find a container that matches the given configuration hash.
        
        Args:
            config_hash: Hash of configuration to match
            docker_utils: DockerUtils instance to check running containers
            
        Returns:
            Container ID if found, None otherwise
        """
        for container_id, data in self.containers.items():
            if data["config_hash"] == config_hash and docker_utils.is_container_running(container_id):
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
        while port in self.port_map or docker_utils.is_port_in_use(port):
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
        for container_id in self.containers:
            if not docker_utils.is_container_running(container_id):
                to_remove.append(container_id)
                
        for container_id in to_remove:
            self.unregister_container(container_id)