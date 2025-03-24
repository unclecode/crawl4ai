import os
import json
import asyncio
import hashlib
import tempfile
import shutil
import socket
import subprocess
from typing import Dict, List, Optional, Tuple, Union

class DockerUtils:
    """Utility class for Docker operations in browser automation.
    
    This class provides methods for managing Docker images, containers,
    and related operations needed for browser automation. It handles
    image building, container lifecycle, port management, and registry operations.
    
    Attributes:
        DOCKER_FOLDER (str): Path to folder containing Docker files
        DOCKER_CONNECT_FILE (str): Path to Dockerfile for connect mode
        DOCKER_LAUNCH_FILE (str): Path to Dockerfile for launch mode
        DOCKER_START_SCRIPT (str): Path to startup script for connect mode
        DEFAULT_CONNECT_IMAGE (str): Default image name for connect mode
        DEFAULT_LAUNCH_IMAGE (str): Default image name for launch mode
        logger: Optional logger instance
    """
    
    # File paths for Docker resources
    DOCKER_FOLDER = os.path.join(os.path.dirname(__file__), "docker")
    DOCKER_CONNECT_FILE = os.path.join(DOCKER_FOLDER, "connect.Dockerfile")
    DOCKER_LAUNCH_FILE = os.path.join(DOCKER_FOLDER, "launch.Dockerfile")
    DOCKER_START_SCRIPT = os.path.join(DOCKER_FOLDER, "start.sh")
    
    # Default image names
    DEFAULT_CONNECT_IMAGE = "crawl4ai/browser-connect:latest"
    DEFAULT_LAUNCH_IMAGE = "crawl4ai/browser-launch:latest"
    
    def __init__(self, logger=None):
        """Initialize Docker utilities.
        
        Args:
            logger: Optional logger for recording operations
        """
        self.logger = logger
    
    # Image Management Methods
    
    async def check_image_exists(self, image_name: str) -> bool:
        """Check if a Docker image exists.
        
        Args:
            image_name: Name of the Docker image to check
            
        Returns:
            bool: True if the image exists, False otherwise
        """
        cmd = ["docker", "image", "inspect", image_name]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            _, _ = await process.communicate()
            return process.returncode == 0
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Error checking if image exists: {str(e)}", tag="DOCKER")
            return False
    
    async def build_docker_image(self, image_name: str, dockerfile_path: str, 
                              files_to_copy: Dict[str, str] = None) -> bool:
        """Build a Docker image from a Dockerfile.
        
        Args:
            image_name: Name to give the built image
            dockerfile_path: Path to the Dockerfile
            files_to_copy: Dict of {dest_name: source_path} for files to copy to build context
            
        Returns:
            bool: True if image was built successfully, False otherwise
        """
        # Create a temporary build context
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy the Dockerfile
            shutil.copy(dockerfile_path, os.path.join(temp_dir, "Dockerfile"))
            
            # Copy any additional files needed
            if files_to_copy:
                for dest_name, source_path in files_to_copy.items():
                    shutil.copy(source_path, os.path.join(temp_dir, dest_name))
            
            # Build the image
            cmd = [
                "docker", "build",
                "-t", image_name,
                temp_dir
            ]
            
            if self.logger:
                self.logger.debug(f"Building Docker image with command: {' '.join(cmd)}", tag="DOCKER")
            
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                if self.logger:
                    self.logger.error(
                        message="Failed to build Docker image: {error}",
                        tag="DOCKER",
                        params={"error": stderr.decode()}
                    )
                return False
            
            if self.logger:
                self.logger.success(f"Successfully built Docker image: {image_name}", tag="DOCKER")
            return True
    
    async def ensure_docker_image_exists(self, image_name: str, mode: str = "connect") -> str:
        """Ensure the required Docker image exists, creating it if necessary.
        
        Args:
            image_name: Name of the Docker image
            mode: Either "connect" or "launch" to determine which image to build
            
        Returns:
            str: Name of the available Docker image
            
        Raises:
            Exception: If image doesn't exist and can't be built
        """
        # If image name is not specified, use default based on mode
        if not image_name:
            image_name = self.DEFAULT_CONNECT_IMAGE if mode == "connect" else self.DEFAULT_LAUNCH_IMAGE
        
        # Check if the image already exists
        if await self.check_image_exists(image_name):
            if self.logger:
                self.logger.debug(f"Docker image {image_name} already exists", tag="DOCKER")
            return image_name
        
        # If we're using a custom image that doesn't exist, warn and fail
        if (image_name != self.DEFAULT_CONNECT_IMAGE and image_name != self.DEFAULT_LAUNCH_IMAGE):
            if self.logger:
                self.logger.warning(
                    f"Custom Docker image {image_name} not found and cannot be automatically created",
                    tag="DOCKER"
                )
            raise Exception(f"Docker image {image_name} not found")
        
        # Build the appropriate default image
        if self.logger:
            self.logger.info(f"Docker image {image_name} not found, creating it now...", tag="DOCKER")
        
        if mode == "connect":
            success = await self.build_docker_image(
                image_name, 
                self.DOCKER_CONNECT_FILE, 
                {"start.sh": self.DOCKER_START_SCRIPT}
            )
        else:
            success = await self.build_docker_image(
                image_name, 
                self.DOCKER_LAUNCH_FILE
            )
        
        if not success:
            raise Exception(f"Failed to create Docker image {image_name}")
        
        return image_name
    
    # Container Management Methods
    
    async def create_container(self, image_name: str, host_port: int, 
                            container_name: Optional[str] = None,
                            volumes: List[str] = None,
                            network: Optional[str] = None,
                            env_vars: Dict[str, str] = None,
                            extra_args: List[str] = None) -> Optional[str]:
        """Create a new Docker container.
        
        Args:
            image_name: Docker image to use
            host_port: Port on host to map to container port 9223
            container_name: Optional name for the container
            volumes: List of volume mappings (e.g., ["host_path:container_path"])
            network: Optional Docker network to use
            env_vars: Dictionary of environment variables
            extra_args: Additional docker run arguments
            
        Returns:
            str: Container ID if successful, None otherwise
        """
        # Prepare container command
        cmd = [
            "docker", "run",
            "--detach",
        ]
        
        # Add container name if specified
        if container_name:
            cmd.extend(["--name", container_name])
        
        # Add port mapping
        cmd.extend(["-p", f"{host_port}:9223"])
        
        # Add volumes
        if volumes:
            for volume in volumes:
                cmd.extend(["-v", volume])
        
        # Add network if specified
        if network:
            cmd.extend(["--network", network])
        
        # Add environment variables
        if env_vars:
            for key, value in env_vars.items():
                cmd.extend(["-e", f"{key}={value}"])
        
        # Add extra args
        if extra_args:
            cmd.extend(extra_args)
        
        # Add image
        cmd.append(image_name)
        
        if self.logger:
            self.logger.debug(f"Creating Docker container with command: {' '.join(cmd)}", tag="DOCKER")
        
        # Run docker command
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                if self.logger:
                    self.logger.error(
                        message="Failed to create Docker container: {error}",
                        tag="DOCKER",
                        params={"error": stderr.decode()}
                    )
                return None
            
            # Get container ID
            container_id = stdout.decode().strip()
            
            if self.logger:
                self.logger.success(f"Created Docker container: {container_id[:12]}", tag="DOCKER")
            
            return container_id
            
        except Exception as e:
            if self.logger:
                self.logger.error(
                    message="Error creating Docker container: {error}",
                    tag="DOCKER",
                    params={"error": str(e)}
                )
            return None
    
    async def is_container_running(self, container_id: str) -> bool:
        """Check if a container is running.
        
        Args:
            container_id: ID of the container to check
            
        Returns:
            bool: True if the container is running, False otherwise
        """
        cmd = ["docker", "inspect", "--format", "{{.State.Running}}", container_id]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            
            return process.returncode == 0 and stdout.decode().strip() == "true"
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Error checking if container is running: {str(e)}", tag="DOCKER")
            return False
    
    async def wait_for_container_ready(self, container_id: str, timeout: int = 30) -> bool:
        """Wait for the container to be in running state.
        
        Args:
            container_id: ID of the container to wait for
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if container is ready, False if timeout occurred
        """
        for _ in range(timeout):
            if await self.is_container_running(container_id):
                return True
            await asyncio.sleep(1)
        
        if self.logger:
            self.logger.warning(f"Container {container_id[:12]} not ready after {timeout}s timeout", tag="DOCKER")
        return False
    
    async def stop_container(self, container_id: str) -> bool:
        """Stop a Docker container.
        
        Args:
            container_id: ID of the container to stop
            
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        cmd = ["docker", "stop", container_id]
        
        try:
            process = await asyncio.create_subprocess_exec(*cmd)
            await process.communicate()
            
            if self.logger:
                self.logger.debug(f"Stopped container: {container_id[:12]}", tag="DOCKER")
                
            return process.returncode == 0
        except Exception as e:
            if self.logger:
                self.logger.warning(
                    message="Failed to stop container: {error}",
                    tag="DOCKER",
                    params={"error": str(e)}
                )
            return False
    
    async def remove_container(self, container_id: str, force: bool = True) -> bool:
        """Remove a Docker container.
        
        Args:
            container_id: ID of the container to remove
            force: Whether to force removal
            
        Returns:
            bool: True if removed successfully, False otherwise
        """
        cmd = ["docker", "rm"]
        if force:
            cmd.append("-f")
        cmd.append(container_id)
        
        try:
            process = await asyncio.create_subprocess_exec(*cmd)
            await process.communicate()
            
            if self.logger:
                self.logger.debug(f"Removed container: {container_id[:12]}", tag="DOCKER")
                
            return process.returncode == 0
        except Exception as e:
            if self.logger:
                self.logger.warning(
                    message="Failed to remove container: {error}",
                    tag="DOCKER",
                    params={"error": str(e)}
                )
            return False
    
    # Container Command Execution Methods
    
    async def exec_in_container(self, container_id: str, command: List[str], 
                             detach: bool = False) -> Tuple[int, str, str]:
        """Execute a command in a running container.
        
        Args:
            container_id: ID of the container
            command: Command to execute as a list of strings
            detach: Whether to run the command in detached mode
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        cmd = ["docker", "exec"]
        if detach:
            cmd.append("-d")
        cmd.append(container_id)
        cmd.extend(command)
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            return process.returncode, stdout.decode(), stderr.decode()
        except Exception as e:
            if self.logger:
                self.logger.error(
                    message="Error executing command in container: {error}",
                    tag="DOCKER",
                    params={"error": str(e)}
                )
            return -1, "", str(e)
    
    async def start_socat_in_container(self, container_id: str) -> bool:
        """Start socat in the container to map port 9222 to 9223.
        
        Args:
            container_id: ID of the container
            
        Returns:
            bool: True if socat started successfully, False otherwise
        """
        # Command to run socat as a background process
        cmd = ["socat", "TCP-LISTEN:9223,fork", "TCP:localhost:9222"]
        
        returncode, _, stderr = await self.exec_in_container(container_id, cmd, detach=True)
        
        if returncode != 0:
            if self.logger:
                self.logger.error(
                    message="Failed to start socat in container: {error}",
                    tag="DOCKER",
                    params={"error": stderr}
                )
            return False
            
        if self.logger:
            self.logger.debug(f"Started socat in container: {container_id[:12]}", tag="DOCKER")
        
        # Wait a moment for socat to start
        await asyncio.sleep(1)
        return True
    
    async def launch_chrome_in_container(self, container_id: str, browser_args: List[str]) -> bool:
        """Launch Chrome inside the container with specified arguments.
        
        Args:
            container_id: ID of the container
            browser_args: Chrome command line arguments
            
        Returns:
            bool: True if Chrome started successfully, False otherwise
        """
        # Build Chrome command
        chrome_cmd = ["google-chrome"]
        chrome_cmd.extend(browser_args)
        
        returncode, _, stderr = await self.exec_in_container(container_id, chrome_cmd, detach=True)
        
        if returncode != 0:
            if self.logger:
                self.logger.error(
                    message="Failed to launch Chrome in container: {error}",
                    tag="DOCKER",
                    params={"error": stderr}
                )
            return False
            
        if self.logger:
            self.logger.debug(f"Launched Chrome in container: {container_id[:12]}", tag="DOCKER")
        
        return True
    
    async def get_process_id_in_container(self, container_id: str, process_name: str) -> Optional[int]:
        """Get the process ID for a process in the container.
        
        Args:
            container_id: ID of the container
            process_name: Name pattern to search for
            
        Returns:
            int: Process ID if found, None otherwise
        """
        cmd = ["pgrep", "-f", process_name]
        
        returncode, stdout, _ = await self.exec_in_container(container_id, cmd)
        
        if returncode == 0 and stdout.strip():
            pid = int(stdout.strip().split("\n")[0])
            return pid
        
        return None
    
    async def stop_process_in_container(self, container_id: str, pid: int) -> bool:
        """Stop a process in the container by PID.
        
        Args:
            container_id: ID of the container
            pid: Process ID to stop
            
        Returns:
            bool: True if process was stopped, False otherwise
        """
        cmd = ["kill", "-TERM", str(pid)]
        
        returncode, _, stderr = await self.exec_in_container(container_id, cmd)
        
        if returncode != 0:
            if self.logger:
                self.logger.warning(
                    message="Failed to stop process in container: {error}",
                    tag="DOCKER",
                    params={"error": stderr}
                )
            return False
            
        if self.logger:
            self.logger.debug(f"Stopped process {pid} in container: {container_id[:12]}", tag="DOCKER")
        
        return True
    
    # Network and Port Methods
    
    async def wait_for_cdp_ready(self, host_port: int, timeout: int = 30) -> bool:
        """Wait for the CDP endpoint to be ready.
        
        Args:
            host_port: Port to check for CDP endpoint
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if CDP endpoint is ready, False if timeout occurred
        """
        import aiohttp
        
        url = f"http://localhost:{host_port}/json/version"
        
        for _ in range(timeout):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=1) as response:
                        if response.status == 200:
                            if self.logger:
                                self.logger.debug(f"CDP endpoint ready on port {host_port}", tag="DOCKER")
                            return True
            except Exception:
                pass
            await asyncio.sleep(1)
        
        if self.logger:
            self.logger.warning(f"CDP endpoint not ready on port {host_port} after {timeout}s timeout", tag="DOCKER")
        return False
    
    def is_port_in_use(self, port: int) -> bool:
        """Check if a port is already in use on the host.
        
        Args:
            port: Port number to check
            
        Returns:
            bool: True if port is in use, False otherwise
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    def get_next_available_port(self, start_port: int = 9223) -> int:
        """Get the next available port starting from a given port.
        
        Args:
            start_port: Port number to start checking from
            
        Returns:
            int: First available port number
        """
        port = start_port
        while self.is_port_in_use(port):
            port += 1
        return port
    
    # Configuration Hash Methods
    
    def generate_config_hash(self, config_dict: Dict) -> str:
        """Generate a hash of the configuration for container matching.
        
        Args:
            config_dict: Dictionary of configuration parameters
            
        Returns:
            str: Hash string uniquely identifying this configuration
        """
        # Convert to canonical JSON string and hash
        config_json = json.dumps(config_dict, sort_keys=True)
        return hashlib.sha256(config_json.encode()).hexdigest()