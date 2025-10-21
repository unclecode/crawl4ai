"""
Crawl4AI Docker Server Manager

Orchestrates single-node Docker deployments with automatic scaling:
- Single container (N=1)
- Docker Swarm (N>1, if available)
- Docker Compose + Nginx (N>1, fallback)
"""

import json
import subprocess
import time
import re
import os
from pathlib import Path
from typing import Dict, Optional, Literal
from datetime import datetime
import socket


ServerMode = Literal["single", "swarm", "compose"]


# ========== Input Validation Functions ==========

def validate_docker_image(image: str) -> bool:
    """Validate Docker image name format.

    Allows: registry.com/namespace/repo:tag
    Format: [registry/][namespace/]repo[:tag][@digest]

    Args:
        image: Docker image string

    Returns:
        True if valid, False otherwise
    """
    if not image or not isinstance(image, str):
        return False

    # Length check
    if len(image) > 256:
        return False

    # Basic pattern: alphanumeric, dots, slashes, colons, dashes, underscores
    # No shell metacharacters allowed
    pattern = r'^[a-zA-Z0-9.\-/:_@]+$'
    if not re.match(pattern, image):
        return False

    # Additional safety: no consecutive special chars that could be exploited
    if '..' in image or '//' in image:
        return False

    return True


def validate_port(port: int) -> bool:
    """Validate port number is in valid range.

    Args:
        port: Port number

    Returns:
        True if valid (1-65535), False otherwise
    """
    return isinstance(port, int) and 1 <= port <= 65535


def validate_env_file(path: str) -> bool:
    """Validate environment file path exists and is readable.

    Args:
        path: File path to validate

    Returns:
        True if file exists and is readable, False otherwise
    """
    if not path or not isinstance(path, str):
        return False

    try:
        file_path = Path(path).resolve()
        return file_path.exists() and file_path.is_file() and os.access(file_path, os.R_OK)
    except Exception:
        return False


def validate_replicas(replicas: int) -> bool:
    """Validate replica count is in reasonable range.

    Args:
        replicas: Number of replicas

    Returns:
        True if valid (1-100), False otherwise
    """
    return isinstance(replicas, int) and 1 <= replicas <= 100


class ServerManager:
    """Manages Crawl4AI Docker server lifecycle and orchestration."""

    def __init__(self):
        self.state_dir = Path.home() / ".crawl4ai" / "server"
        self.state_file = self.state_dir / "state.json"
        self.compose_file = self.state_dir / "docker-compose.yml"
        self.nginx_conf = self.state_dir / "nginx.conf"
        self.state_dir.mkdir(parents=True, exist_ok=True)

    # ========== Public API ==========

    async def start(
        self,
        replicas: int = 1,
        mode: str = "auto",
        port: int = 11235,
        env_file: Optional[str] = None,
        image: str = "unclecode/crawl4ai:latest",
        **kwargs
    ) -> Dict:
        """Start Crawl4AI server with specified configuration.

        Args:
            replicas: Number of container replicas (default: 1)
            mode: Deployment mode - 'auto', 'single', 'swarm', or 'compose'
            port: External port to expose (default: 11235)
            env_file: Path to environment file
            image: Docker image to use
            **kwargs: Additional docker run arguments

        Returns:
            Dict with status and deployment info
        """
        # Check if already running
        state = self._load_state()
        if state:
            return {
                "success": False,
                "message": "Server already running",
                "current_state": state
            }

        # Validate Docker is available
        if not self._is_docker_available():
            return {
                "success": False,
                "error": "Docker daemon not running. Please start Docker first."
            }

        # Check port availability
        if not self._is_port_available(port):
            return {
                "success": False,
                "error": f"Port {port} is already in use"
            }

        # Detect deployment mode
        detected_mode = self._detect_mode(replicas, mode)

        # Ensure image is available
        if not self._ensure_image(image):
            return {
                "success": False,
                "error": f"Failed to pull image {image}"
            }

        # Start based on mode
        if detected_mode == "single":
            result = self._start_single(port, env_file, image, **kwargs)
        elif detected_mode == "swarm":
            result = self._start_swarm(replicas, port, env_file, image, **kwargs)
        elif detected_mode == "compose":
            result = self._start_compose(replicas, port, env_file, image, **kwargs)
        else:
            return {
                "success": False,
                "error": f"Unknown mode: {detected_mode}"
            }

        if result["success"]:
            # Save state
            self._save_state({
                "mode": detected_mode,
                "replicas": replicas,
                "port": port,
                "image": image,
                "env_file": env_file,
                "started_at": datetime.now().isoformat(),
                **result.get("state_data", {})
            })

        return result

    async def status(self) -> Dict:
        """Get current server status."""
        state = self._load_state()

        if not state:
            return {
                "running": False,
                "message": "No server is currently running"
            }

        mode = state["mode"]

        # Check actual container status
        if mode == "single":
            running = self._check_container_running(state.get("container_id"))
        elif mode == "swarm":
            running = self._check_service_running(state.get("service_name"))
        elif mode == "compose":
            running = self._check_compose_running(state.get("compose_project"))
        else:
            running = False

        if not running:
            # State file exists but containers are gone - clean up
            self._clear_state()
            return {
                "running": False,
                "message": "State file exists but containers stopped externally"
            }

        return {
            "running": True,
            "mode": mode,
            "replicas": state.get("replicas", 1),
            "port": state.get("port", 11235),
            "image": state.get("image"),
            "started_at": state.get("started_at"),
            "uptime": self._calculate_uptime(state.get("started_at"))
        }

    async def stop(self, remove_volumes: bool = False) -> Dict:
        """Stop running server.

        Args:
            remove_volumes: Remove associated volumes

        Returns:
            Dict with stop status
        """
        state = self._load_state()

        if not state:
            return {
                "success": False,
                "message": "No server is running"
            }

        mode = state["mode"]

        try:
            if mode == "single":
                self._stop_single(state.get("container_id"), remove_volumes)
            elif mode == "swarm":
                self._stop_swarm(state.get("service_name"))
            elif mode == "compose":
                self._stop_compose(state.get("compose_project"), remove_volumes)

            self._clear_state()

            return {
                "success": True,
                "message": f"Server stopped ({mode} mode)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def cleanup(self, force: bool = False) -> Dict:
        """Force cleanup of all Crawl4AI Docker resources.

        Args:
            force: Force cleanup even if state file doesn't exist

        Returns:
            Dict with cleanup status
        """
        import logging
        logger = logging.getLogger(__name__)

        removed_count = 0
        messages = []

        try:
            # Try to stop via state file first
            if not force:
                state = self._load_state()
                if state:
                    stop_result = await self.stop(remove_volumes=True)
                    if stop_result["success"]:
                        return {
                            "success": True,
                            "removed": 1,
                            "message": "Stopped via state file"
                        }

            # Force cleanup - find and remove all Crawl4AI resources
            logger.info("Force cleanup: removing all Crawl4AI Docker resources")

            # Remove all crawl4ai containers
            try:
                result = subprocess.run(
                    ["docker", "ps", "-a", "--filter", "name=crawl4ai", "--format", "{{.ID}}"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                container_ids = result.stdout.strip().split('\n')
                container_ids = [cid for cid in container_ids if cid]

                for cid in container_ids:
                    subprocess.run(["docker", "rm", "-f", cid], capture_output=True, timeout=10)
                    removed_count += 1
                messages.append(f"Removed {len(container_ids)} crawl4ai containers")
            except Exception as e:
                logger.warning(f"Error removing containers: {e}")

            # Remove nginx containers
            try:
                result = subprocess.run(
                    ["docker", "ps", "-a", "--filter", "name=nginx", "--format", "{{.ID}}"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                nginx_ids = result.stdout.strip().split('\n')
                nginx_ids = [nid for nid in nginx_ids if nid]

                for nid in nginx_ids:
                    subprocess.run(["docker", "rm", "-f", nid], capture_output=True, timeout=10)
                    removed_count += len(nginx_ids)
                if nginx_ids:
                    messages.append(f"Removed {len(nginx_ids)} nginx containers")
            except Exception as e:
                logger.warning(f"Error removing nginx: {e}")

            # Remove redis containers
            try:
                result = subprocess.run(
                    ["docker", "ps", "-a", "--filter", "name=redis", "--format", "{{.ID}}"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                redis_ids = result.stdout.strip().split('\n')
                redis_ids = [rid for rid in redis_ids if rid]

                for rid in redis_ids:
                    subprocess.run(["docker", "rm", "-f", rid], capture_output=True, timeout=10)
                    removed_count += len(redis_ids)
                if redis_ids:
                    messages.append(f"Removed {len(redis_ids)} redis containers")
            except Exception as e:
                logger.warning(f"Error removing redis: {e}")

            # Clean up compose projects
            for project in ["crawl4ai", "fix-docker"]:
                try:
                    subprocess.run(
                        ["docker", "compose", "-p", project, "down", "-v"],
                        capture_output=True,
                        timeout=30,
                        cwd=str(self.state_dir)
                    )
                    messages.append(f"Cleaned compose project: {project}")
                except Exception:
                    pass

            # Remove networks
            try:
                subprocess.run(["docker", "network", "prune", "-f"], capture_output=True, timeout=10)
                messages.append("Pruned networks")
            except Exception as e:
                logger.warning(f"Error pruning networks: {e}")

            # Clear state file
            self._clear_state()
            messages.append("Cleared state file")

            return {
                "success": True,
                "removed": removed_count,
                "message": "; ".join(messages)
            }

        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return {
                "success": False,
                "message": f"Cleanup failed: {str(e)}"
            }

    async def scale(self, replicas: int) -> Dict:
        """Scale server to specified replica count.

        Args:
            replicas: Target number of replicas

        Returns:
            Dict with scaling status
        """
        state = self._load_state()

        if not state:
            return {
                "success": False,
                "message": "No server is running"
            }

        mode = state["mode"]

        if mode == "single":
            return {
                "success": False,
                "error": "Cannot scale single container mode. Use 'crwl server stop' then 'crwl server start --replicas N'"
            }

        try:
            if mode == "swarm":
                self._scale_swarm(state["service_name"], replicas)
            elif mode == "compose":
                self._scale_compose(state["compose_project"], replicas)

            # Update state
            state["replicas"] = replicas
            self._save_state(state)

            return {
                "success": True,
                "message": f"Scaled to {replicas} replicas",
                "mode": mode
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def logs(self, follow: bool = False, tail: int = 100) -> str:
        """Get server logs.

        Args:
            follow: Follow log output
            tail: Number of lines to show

        Returns:
            Log output as string
        """
        state = self._load_state()

        if not state:
            return "No server is running"

        mode = state["mode"]

        try:
            if mode == "single":
                return self._logs_single(state["container_id"], follow, tail)
            elif mode == "swarm":
                return self._logs_swarm(state["service_name"], follow, tail)
            elif mode == "compose":
                return self._logs_compose(state["compose_project"], follow, tail)
        except Exception as e:
            return f"Error getting logs: {e}"

    # ========== Mode Detection ==========

    def _detect_mode(self, replicas: int, mode: str) -> ServerMode:
        """Detect deployment mode based on replicas and user preference."""
        if mode != "auto":
            return mode

        if replicas == 1:
            return "single"

        # N>1: prefer Swarm if available, fallback to Compose
        if self._is_swarm_available():
            return "swarm"

        return "compose"

    def _is_swarm_available(self) -> bool:
        """Check if Docker Swarm is initialized and available."""
        try:
            result = subprocess.run(
                ["docker", "info", "--format", "{{.Swarm.LocalNodeState}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() == "active"
        except Exception:
            return False

    def _is_docker_available(self) -> bool:
        """Check if Docker daemon is running."""
        try:
            subprocess.run(
                ["docker", "ps"],
                capture_output=True,
                timeout=5,
                check=True
            )
            return True
        except Exception:
            return False

    def _is_port_available(self, port: int) -> bool:
        """Check if port is available for binding."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('0.0.0.0', port))
                return True
            except OSError:
                return False

    def _ensure_image(self, image: str) -> bool:
        """Ensure Docker image is available locally, pull if needed."""
        try:
            # Check if image exists locally
            result = subprocess.run(
                ["docker", "image", "inspect", image],
                capture_output=True,
                timeout=5
            )

            if result.returncode == 0:
                return True

            # Determine if this looks like a registry image
            # Registry images have format: [registry/][namespace/]repository[:tag]
            # Examples: unclecode/crawl4ai:latest, docker.io/library/nginx:latest
            # Local-only: crawl4ai-local:latest, my-image:v1

            # If it has a dot in the first part (before any slash), it's likely a registry
            # Or if it has a slash, it's likely registry/namespace/repo format
            parts = image.split("/")
            is_registry_image = (
                len(parts) > 1 and  # Has slash
                "." not in parts[0] and  # First part isn't a domain (localhost.localdomain)
                not parts[0].startswith("localhost")  # Not localhost registry
            )

            if not is_registry_image:
                return False  # Local image doesn't exist

            # Try to pull from registry
            subprocess.run(
                ["docker", "pull", image],
                capture_output=True,
                check=True,
                timeout=300
            )
            return True
        except Exception:
            return False

    # ========== Single Container Mode ==========

    def _start_single(self, port: int, env_file: Optional[str], image: str, **kwargs) -> Dict:
        """Start single container with docker run."""
        # Validate inputs to prevent injection attacks
        if not validate_port(port):
            return {
                "success": False,
                "error": f"Invalid port number: {port}. Must be between 1-65535."
            }

        if not validate_docker_image(image):
            return {
                "success": False,
                "error": f"Invalid Docker image format: {image}"
            }

        if env_file and not validate_env_file(env_file):
            return {
                "success": False,
                "error": f"Environment file not found or not readable: {env_file}"
            }

        cmd = [
            "docker", "run",
            "-d",  # Detached
            "--name", "crawl4ai_server",
            "-p", f"{port}:11235",
            "--shm-size=1g",  # Important for browser
        ]

        if env_file:
            # Use absolute path to prevent path traversal
            abs_env_file = str(Path(env_file).resolve())
            cmd.extend(["--env-file", abs_env_file])

        # Whitelist allowed Docker flags to prevent privilege escalation
        allowed_flags = {"--memory", "--cpus", "--restart", "--network"}
        for key, value in kwargs.items():
            if key in allowed_flags:
                cmd.append(key)
                if value is not True:  # Handle boolean flags
                    cmd.append(str(value))
            else:
                # Log ignored flags for debugging
                import logging
                logging.warning(f"Ignoring non-whitelisted Docker flag: {key}")

        cmd.append(image)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            container_id = result.stdout.strip()

            # Wait for health check
            if self._wait_for_health(f"http://localhost:{port}/health"):
                return {
                    "success": True,
                    "message": f"Server started on port {port}",
                    "state_data": {"container_id": container_id}
                }
            else:
                # Cleanup failed container
                subprocess.run(["docker", "rm", "-f", container_id], capture_output=True)
                return {
                    "success": False,
                    "error": "Container started but health check failed"
                }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Failed to start container: {e.stderr}"
            }

    def _stop_single(self, container_id: str, remove_volumes: bool):
        """Stop single container."""
        cmd = ["docker", "rm", "-f"]
        if remove_volumes:
            cmd.append("-v")
        cmd.append(container_id)
        subprocess.run(cmd, check=True)

    def _check_container_running(self, container_id: str) -> bool:
        """Check if container is running."""
        if not container_id:
            return False
        try:
            result = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Running}}", container_id],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() == "true"
        except Exception:
            return False

    def _logs_single(self, container_id: str, follow: bool, tail: int) -> str:
        """Get logs from single container."""
        cmd = ["docker", "logs", "--tail", str(tail)]
        if follow:
            cmd.append("-f")
        cmd.append(container_id)

        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout

    # ========== Swarm Mode ==========

    def _start_swarm(self, replicas: int, port: int, env_file: Optional[str], image: str, **kwargs) -> Dict:
        """Start service in Swarm mode."""
        # Validate inputs to prevent injection attacks
        if not validate_replicas(replicas):
            return {
                "success": False,
                "error": f"Invalid replica count: {replicas}. Must be between 1-100."
            }

        if not validate_port(port):
            return {
                "success": False,
                "error": f"Invalid port number: {port}. Must be between 1-65535."
            }

        if not validate_docker_image(image):
            return {
                "success": False,
                "error": f"Invalid Docker image format: {image}"
            }

        if env_file and not validate_env_file(env_file):
            return {
                "success": False,
                "error": f"Environment file not found or not readable: {env_file}"
            }

        service_name = "crawl4ai"  # Static name (safe)

        # Initialize swarm if needed
        if not self._is_swarm_available():
            init_result = self._init_swarm()
            if not init_result:
                return {
                    "success": False,
                    "error": "Failed to initialize Docker Swarm. Use 'docker swarm init' manually."
                }

        cmd = [
            "docker", "service", "create",
            "--name", service_name,
            "--replicas", str(replicas),
            "--publish", f"{port}:11235",
            "--mount", "type=tmpfs,target=/dev/shm,tmpfs-size=1g",
            "--limit-memory", "4G",
        ]

        if env_file:
            # Use absolute path to prevent path traversal
            abs_env_file = str(Path(env_file).resolve())
            cmd.extend(["--env-file", abs_env_file])

        cmd.append(image)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            service_id = result.stdout.strip()

            # Wait for service to be ready (check replicas)
            if self._wait_for_service(service_name, replicas):
                return {
                    "success": True,
                    "message": f"Swarm service started with {replicas} replicas",
                    "state_data": {
                        "service_name": service_name,
                        "service_id": service_id
                    }
                }
            else:
                # Cleanup failed service
                subprocess.run(["docker", "service", "rm", service_name], capture_output=True)
                return {
                    "success": False,
                    "error": "Service created but replicas failed to start"
                }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Failed to create Swarm service: {e.stderr}"
            }

    def _init_swarm(self) -> bool:
        """Initialize Docker Swarm if not already initialized."""
        try:
            result = subprocess.run(
                ["docker", "swarm", "init"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

    def _wait_for_service(self, service_name: str, expected_replicas: int, timeout: int = 60) -> bool:
        """Wait for Swarm service replicas to be running."""
        import time
        start = time.time()

        while time.time() - start < timeout:
            try:
                result = subprocess.run(
                    ["docker", "service", "ls", "--filter", f"name={service_name}", "--format", "{{.Replicas}}"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0:
                    # Format is "2/3" (running/desired)
                    replicas_str = result.stdout.strip()
                    if "/" in replicas_str:
                        running, desired = replicas_str.split("/")
                        if int(running) == expected_replicas and int(desired) == expected_replicas:
                            return True

                time.sleep(2)
            except Exception:
                time.sleep(2)

        return False

    def _stop_swarm(self, service_name: str):
        """Stop Swarm service."""
        subprocess.run(
            ["docker", "service", "rm", service_name],
            check=True,
            capture_output=True
        )

    def _scale_swarm(self, service_name: str, replicas: int):
        """Scale Swarm service."""
        subprocess.run(
            ["docker", "service", "scale", f"{service_name}={replicas}"],
            check=True,
            capture_output=True
        )

    def _check_service_running(self, service_name: str) -> bool:
        """Check if Swarm service is running."""
        if not service_name:
            return False
        try:
            result = subprocess.run(
                ["docker", "service", "ls", "--filter", f"name={service_name}", "--format", "{{.Name}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return service_name in result.stdout
        except Exception:
            return False

    def _logs_swarm(self, service_name: str, follow: bool, tail: int) -> str:
        """Get logs from Swarm service."""
        cmd = ["docker", "service", "logs", "--tail", str(tail)]
        if follow:
            cmd.append("-f")
        cmd.append(service_name)

        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout

    # ========== Compose Mode ==========

    def _start_compose(self, replicas: int, port: int, env_file: Optional[str], image: str, **kwargs) -> Dict:
        """Start with Docker Compose + Nginx."""
        # Validate inputs to prevent injection attacks
        if not validate_replicas(replicas):
            return {
                "success": False,
                "error": f"Invalid replica count: {replicas}. Must be between 1-100."
            }

        if not validate_port(port):
            return {
                "success": False,
                "error": f"Invalid port number: {port}. Must be between 1-65535."
            }

        if not validate_docker_image(image):
            return {
                "success": False,
                "error": f"Invalid Docker image format: {image}"
            }

        if env_file and not validate_env_file(env_file):
            return {
                "success": False,
                "error": f"Environment file not found or not readable: {env_file}"
            }

        project_name = "crawl4ai"  # Static name (safe)

        # Generate compose and nginx config files
        try:
            self._generate_compose_file(replicas, port, env_file or "", image)
            self._generate_nginx_config()
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate config files: {e}"
            }

        # Start compose stack - use absolute path for compose file
        cmd = [
            "docker", "compose",
            "-f", str(self.compose_file.resolve()),
            "-p", project_name,
            "up", "-d",
            "--scale", f"crawl4ai={replicas}"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=str(self.state_dir))

            # Wait for services to be healthy
            if self._wait_for_compose_healthy(project_name, timeout=60):
                return {
                    "success": True,
                    "message": f"Compose stack started with {replicas} replicas",
                    "state_data": {
                        "compose_project": project_name
                    }
                }
            else:
                # Cleanup failed deployment
                subprocess.run(
                    ["docker", "compose", "-f", str(self.compose_file), "-p", project_name, "down"],
                    capture_output=True,
                    cwd=str(self.state_dir)
                )
                return {
                    "success": False,
                    "error": "Compose stack started but health checks failed"
                }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Failed to start Compose stack: {e.stderr}"
            }

    def _generate_compose_file(self, replicas: int, port: int, env_file: str, image: str):
        """Generate docker-compose.yml from template with validation."""
        import os

        # Get template path - check if we're in the package or dev environment
        template_path = Path(__file__).parent / "templates" / "docker-compose.template.yml"

        if not template_path.exists():
            raise FileNotFoundError(
                f"Docker Compose template not found: {template_path}\n"
                f"Please ensure crawl4ai package is correctly installed.\n"
                f"Try: pip install --force-reinstall crawl4ai"
            )

        try:
            with open(template_path) as f:
                template = f.read()
        except IOError as e:
            raise RuntimeError(f"Failed to read template {template_path}: {e}")

        # Validate template has required placeholders
        required_vars = {"${IMAGE}", "${REPLICAS}", "${PORT}", "${NGINX_CONF}"}
        missing = required_vars - set(re.findall(r'\$\{[A-Z_]+\}', template))
        if missing:
            raise ValueError(f"Template missing required variables: {missing}")

        # Substitute variables
        content = template.replace("${IMAGE}", image)
        content = content.replace("${REPLICAS}", str(replicas))
        content = content.replace("${PORT}", str(port))
        content = content.replace("${NGINX_CONF}", str(self.nginx_conf))

        # Verify no unsubstituted variables remain
        remaining = re.findall(r'\$\{[A-Z_]+\}', content)
        if remaining:
            import logging
            logging.warning(f"Unsubstituted variables in template: {remaining}")

        try:
            with open(self.compose_file, "w") as f:
                f.write(content)
        except IOError as e:
            raise RuntimeError(f"Failed to write compose file {self.compose_file}: {e}")

    def _generate_nginx_config(self):
        """Generate nginx.conf from template with validation."""
        template_path = Path(__file__).parent / "templates" / "nginx.conf.template"

        if not template_path.exists():
            raise FileNotFoundError(
                f"Nginx template not found: {template_path}\n"
                f"Please ensure crawl4ai package is correctly installed.\n"
                f"Try: pip install --force-reinstall crawl4ai"
            )

        try:
            with open(template_path) as f:
                content = f.read()
        except IOError as e:
            raise RuntimeError(f"Failed to read nginx template {template_path}: {e}")

        # Nginx template doesn't need variable substitution currently
        try:
            with open(self.nginx_conf, "w") as f:
                f.write(content)
        except IOError as e:
            raise RuntimeError(f"Failed to write nginx config {self.nginx_conf}: {e}")

    def _wait_for_compose_healthy(self, project: str, timeout: int = 60) -> bool:
        """Wait for Compose services to be healthy."""
        import time
        start = time.time()

        while time.time() - start < timeout:
            try:
                # Check if nginx service is running (it depends on crawl4ai)
                result = subprocess.run(
                    ["docker", "compose", "-f", str(self.compose_file), "-p", project, "ps", "--format", "json"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    cwd=str(self.state_dir)
                )

                if result.returncode == 0 and result.stdout:
                    import json
                    services = [json.loads(line) for line in result.stdout.strip().split('\n') if line]

                    # Check if nginx is running (implies crawl4ai instances are up)
                    nginx_running = any(
                        s.get("Service") == "nginx" and s.get("State") == "running"
                        for s in services
                    )

                    if nginx_running:
                        return True

                time.sleep(2)
            except Exception:
                time.sleep(2)

        return False

    def _stop_compose(self, project: str, remove_volumes: bool):
        """Stop Compose stack."""
        cmd = ["docker", "compose", "-f", str(self.compose_file), "-p", project, "down"]
        if remove_volumes:
            cmd.append("-v")

        subprocess.run(cmd, check=True, capture_output=True, cwd=str(self.state_dir))

    def _scale_compose(self, project: str, replicas: int):
        """Scale Compose service."""
        subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "-p", project, "up", "-d", "--scale", f"crawl4ai={replicas}", "--no-recreate"],
            check=True,
            capture_output=True,
            cwd=str(self.state_dir)
        )

    def _check_compose_running(self, project: str) -> bool:
        """Check if Compose stack is running."""
        if not project or not self.compose_file.exists():
            return False
        try:
            result = subprocess.run(
                ["docker", "compose", "-f", str(self.compose_file), "-p", project, "ps", "-q"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=str(self.state_dir)
            )
            # If there are any container IDs, the stack is running
            return bool(result.stdout.strip())
        except Exception:
            return False

    def _logs_compose(self, project: str, follow: bool, tail: int) -> str:
        """Get logs from Compose stack."""
        cmd = ["docker", "compose", "-f", str(self.compose_file), "-p", project, "logs", "--tail", str(tail)]
        if follow:
            cmd.append("-f")

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.state_dir))
        return result.stdout

    # ========== State Management ==========

    def _save_state(self, state: Dict):
        """Persist server state to disk with atomic write and file locking."""
        import fcntl

        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Atomic write with exclusive lock
        temp_file = self.state_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock
                json.dump(state, f, indent=2)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Unlock

            # Atomic rename
            temp_file.replace(self.state_file)
        except Exception as e:
            # Cleanup temp file on error
            temp_file.unlink(missing_ok=True)
            raise RuntimeError(f"Failed to save state: {e}")

    def _load_state(self) -> Optional[Dict]:
        """Load server state from disk with file locking."""
        import fcntl

        if not self.state_file.exists():
            return None

        try:
            with open(self.state_file) as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)  # Shared lock (read)
                state = json.load(f)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Unlock
                return state
        except (json.JSONDecodeError, IOError) as e:
            # Log and remove corrupted state file
            import logging
            logging.error(f"Corrupted state file, removing: {e}")
            self.state_file.unlink(missing_ok=True)
            return None

    def _clear_state(self):
        """Remove state file with locking."""
        import fcntl

        if self.state_file.exists():
            try:
                # Acquire lock before deletion to prevent race
                with open(self.state_file, 'r') as f:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    # Lock acquired, now delete
                self.state_file.unlink(missing_ok=True)
            except Exception:
                # If lock fails, force delete anyway
                self.state_file.unlink(missing_ok=True)

    # ========== Helpers ==========

    def _wait_for_health(self, url: str, timeout: int = 30) -> bool:
        """Wait for health endpoint to respond."""
        import urllib.request

        start = time.time()
        while time.time() - start < timeout:
            try:
                urllib.request.urlopen(url, timeout=2)
                return True
            except Exception:
                time.sleep(1)
        return False

    def _calculate_uptime(self, started_at: str) -> str:
        """Calculate uptime from ISO timestamp."""
        if not started_at:
            return "unknown"

        try:
            start = datetime.fromisoformat(started_at)
            delta = datetime.now() - start

            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60

            if delta.days > 0:
                return f"{delta.days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        except Exception:
            return "unknown"
