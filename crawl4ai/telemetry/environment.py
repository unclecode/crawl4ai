"""
Environment detection for Crawl4AI telemetry.
Detects whether we're running in CLI, Docker, Jupyter, etc.
"""

import os
import sys
from enum import Enum
from typing import Optional


class Environment(Enum):
    """Detected runtime environment."""
    CLI = "cli"
    DOCKER = "docker"
    JUPYTER = "jupyter"
    COLAB = "colab"
    API_SERVER = "api_server"
    UNKNOWN = "unknown"


class EnvironmentDetector:
    """Detects the current runtime environment."""
    
    @staticmethod
    def detect() -> Environment:
        """
        Detect current runtime environment.
        
        Returns:
            Environment enum value
        """
        # Check for Docker
        if EnvironmentDetector._is_docker():
            # Further check if it's API server
            if EnvironmentDetector._is_api_server():
                return Environment.API_SERVER
            return Environment.DOCKER
        
        # Check for Google Colab
        if EnvironmentDetector._is_colab():
            return Environment.COLAB
        
        # Check for Jupyter
        if EnvironmentDetector._is_jupyter():
            return Environment.JUPYTER
        
        # Check for CLI
        if EnvironmentDetector._is_cli():
            return Environment.CLI
        
        return Environment.UNKNOWN
    
    @staticmethod
    def _is_docker() -> bool:
        """Check if running inside Docker container."""
        # Check for Docker-specific files
        if os.path.exists('/.dockerenv'):
            return True
        
        # Check cgroup for docker signature
        try:
            with open('/proc/1/cgroup', 'r') as f:
                return 'docker' in f.read()
        except (IOError, OSError):
            pass
        
        # Check environment variable (if set in Dockerfile)
        return os.environ.get('CRAWL4AI_DOCKER', '').lower() == 'true'
    
    @staticmethod
    def _is_api_server() -> bool:
        """Check if running as API server."""
        # Check for API server indicators
        return (
            os.environ.get('CRAWL4AI_API_SERVER', '').lower() == 'true' or
            'deploy/docker/server.py' in ' '.join(sys.argv) or
            'deploy/docker/api.py' in ' '.join(sys.argv)
        )
    
    @staticmethod
    def _is_jupyter() -> bool:
        """Check if running in Jupyter notebook."""
        try:
            # Check for IPython
            from IPython import get_ipython
            ipython = get_ipython()
            
            if ipython is None:
                return False
            
            # Check for notebook kernel
            if 'IPKernelApp' in ipython.config:
                return True
            
            # Check for Jupyter-specific attributes
            if hasattr(ipython, 'kernel'):
                return True
                
        except (ImportError, AttributeError):
            pass
        
        return False
    
    @staticmethod
    def _is_colab() -> bool:
        """Check if running in Google Colab."""
        try:
            import google.colab
            return True
        except ImportError:
            pass
        
        # Alternative check
        return 'COLAB_GPU' in os.environ or 'COLAB_TPU_ADDR' in os.environ
    
    @staticmethod
    def _is_cli() -> bool:
        """Check if running from command line."""
        # Check if we have a terminal
        return (
            hasattr(sys, 'ps1') or 
            sys.stdin.isatty() or
            bool(os.environ.get('TERM'))
        )
    
    @staticmethod
    def is_interactive() -> bool:
        """
        Check if environment supports interactive prompts.
        
        Returns:
            True if interactive prompts are supported
        """
        env = EnvironmentDetector.detect()
        
        # Docker/API server are non-interactive
        if env in [Environment.DOCKER, Environment.API_SERVER]:
            return False
        
        # CLI with TTY is interactive
        if env == Environment.CLI:
            return sys.stdin.isatty()
        
        # Jupyter/Colab can be interactive with widgets
        if env in [Environment.JUPYTER, Environment.COLAB]:
            return True
        
        return False
    
    @staticmethod
    def supports_widgets() -> bool:
        """
        Check if environment supports IPython widgets.
        
        Returns:
            True if widgets are supported
        """
        env = EnvironmentDetector.detect()
        
        if env not in [Environment.JUPYTER, Environment.COLAB]:
            return False
        
        try:
            import ipywidgets
            from IPython.display import display
            return True
        except ImportError:
            return False
    
    @staticmethod
    def get_environment_context() -> dict:
        """
        Get environment context for telemetry.
        
        Returns:
            Dictionary with environment information
        """
        env = EnvironmentDetector.detect()
        
        context = {
            'environment_type': env.value,
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'platform': sys.platform,
        }
        
        # Add environment-specific context
        if env == Environment.DOCKER:
            context['docker'] = True
            context['container_id'] = os.environ.get('HOSTNAME', 'unknown')
        
        elif env == Environment.COLAB:
            context['colab'] = True
            context['gpu'] = bool(os.environ.get('COLAB_GPU'))
        
        elif env == Environment.JUPYTER:
            context['jupyter'] = True
        
        return context