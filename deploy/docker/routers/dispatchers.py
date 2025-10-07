"""
Router for dispatcher management endpoints.

Provides endpoints to:
- List available dispatchers
- Get default dispatcher info
- Get dispatcher statistics
"""

import logging
from typing import Dict, List

from fastapi import APIRouter, HTTPException, Request
from schemas import DispatcherInfo, DispatcherStatsResponse, DispatcherType
from utils import get_available_dispatchers, get_dispatcher_config

logger = logging.getLogger(__name__)

# --- APIRouter for Dispatcher Endpoints ---
router = APIRouter(
    prefix="/dispatchers",
    tags=["Dispatchers"],
)


@router.get("",
    summary="List Dispatchers",
    description="Get information about all available dispatcher types.",
    response_description="List of dispatcher configurations and features",
    response_model=List[DispatcherInfo]
)
async def list_dispatchers(request: Request):
    """
    List all available dispatcher types.
    
    Returns information about each dispatcher type including name, description,
    configuration parameters, and key features.
    
    **Dispatchers:**
    - `memory_adaptive`: Automatically manages crawler instances based on memory
    - `semaphore`: Simple semaphore-based concurrency control
    
    **Response:**
    ```json
    [
        {
            "type": "memory_adaptive",
            "name": "Memory Adaptive Dispatcher",
            "description": "Automatically adjusts crawler pool based on memory usage",
            "config": {...},
            "features": ["Auto-scaling", "Memory monitoring", "Smart throttling"]
        },
        {
            "type": "semaphore",
            "name": "Semaphore Dispatcher",
            "description": "Simple semaphore-based concurrency control",
            "config": {...},
            "features": ["Fixed concurrency", "Simple queue"]
        }
    ]
    ```
    
    **Usage:**
    ```python
    response = requests.get(
        "http://localhost:11235/dispatchers",
        headers={"Authorization": f"Bearer {token}"}
    )
    dispatchers = response.json()
    for dispatcher in dispatchers:
        print(f"{dispatcher['type']}: {dispatcher['description']}")
    ```
    
    **Notes:**
    - Lists all registered dispatcher types
    - Shows configuration options for each
    - Use with /crawl endpoint's `dispatcher` parameter
    """
    try:
        dispatchers_info = get_available_dispatchers()
        
        result = []
        for dispatcher_type, info in dispatchers_info.items():
            result.append(
                DispatcherInfo(
                    type=DispatcherType(dispatcher_type),
                    name=info["name"],
                    description=info["description"],
                    config=info["config"],
                    features=info["features"],
                )
            )
        
        return result
    except Exception as e:
        logger.error(f"Error listing dispatchers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list dispatchers: {str(e)}")


@router.get("/default",
    summary="Get Default Dispatcher",
    description="Get information about the currently configured default dispatcher.",
    response_description="Default dispatcher information",
    response_model=Dict
)
async def get_default_dispatcher(request: Request):
    """
    Get information about the current default dispatcher.
    
    Returns the dispatcher type, configuration, and status for the default
    dispatcher used when no specific dispatcher is requested.
    
    **Response:**
    ```json
    {
        "type": "memory_adaptive",
        "config": {
            "max_memory_percent": 80,
            "check_interval": 10,
            "min_instances": 1,
            "max_instances": 10
        },
        "active": true
    }
    ```
    
    **Usage:**
    ```python
    response = requests.get(
        "http://localhost:11235/dispatchers/default",
        headers={"Authorization": f"Bearer {token}"}
    )
    default_dispatcher = response.json()
    print(f"Default: {default_dispatcher['type']}")
    ```
    
    **Notes:**
    - Shows which dispatcher is used by default
    - Default can be configured via server settings
    - Override with `dispatcher` parameter in /crawl requests
    """
    try:
        default_type = request.app.state.default_dispatcher_type
        dispatcher = request.app.state.dispatchers.get(default_type)
        
        if not dispatcher:
            raise HTTPException(
                status_code=500, 
                detail=f"Default dispatcher '{default_type}' not initialized"
            )
        
        return {
            "type": default_type,
            "config": get_dispatcher_config(default_type),
            "active": True,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting default dispatcher: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get default dispatcher: {str(e)}"
        )


@router.get("/{dispatcher_type}/stats",
    summary="Get Dispatcher Statistics",
    description="Get runtime statistics for a specific dispatcher.",
    response_description="Dispatcher statistics and metrics",
    response_model=DispatcherStatsResponse
)
async def get_dispatcher_stats(dispatcher_type: DispatcherType, request: Request):
    """
    Get runtime statistics for a specific dispatcher.
    
    Returns active sessions, configuration, and dispatcher-specific metrics.
    Useful for monitoring and debugging dispatcher performance.
    
    **Parameters:**
    - `dispatcher_type`: Dispatcher type (memory_adaptive, semaphore)
    
    **Response:**
    ```json
    {
        "type": "memory_adaptive",
        "active_sessions": 3,
        "config": {
            "max_memory_percent": 80,
            "check_interval": 10
        },
        "stats": {
            "current_memory_percent": 45.2,
            "active_instances": 3,
            "max_instances": 10,
            "throttled_count": 0
        }
    }
    ```
    
    **Usage:**
    ```python
    response = requests.get(
        "http://localhost:11235/dispatchers/memory_adaptive/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    stats = response.json()
    print(f"Active sessions: {stats['active_sessions']}")
    print(f"Memory usage: {stats['stats']['current_memory_percent']}%")
    ```
    
    **Notes:**
    - Real-time statistics
    - Stats vary by dispatcher type
    - Use for monitoring and capacity planning
    - Returns 404 if dispatcher type not found
    """
    try:
        dispatcher_name = dispatcher_type.value
        dispatcher = request.app.state.dispatchers.get(dispatcher_name)
        
        if not dispatcher:
            raise HTTPException(
                status_code=404, 
                detail=f"Dispatcher '{dispatcher_name}' not found or not initialized"
            )
        
        # Get basic stats
        stats = {
            "type": dispatcher_type,
            "active_sessions": dispatcher.concurrent_sessions,
            "config": get_dispatcher_config(dispatcher_name),
            "stats": {}
        }
        
        # Add dispatcher-specific stats
        if dispatcher_name == "memory_adaptive":
            stats["stats"] = {
                "current_memory_percent": getattr(dispatcher, "current_memory_percent", 0.0),
                "memory_pressure_mode": getattr(dispatcher, "memory_pressure_mode", False),
                "task_queue_size": dispatcher.task_queue.qsize() if hasattr(dispatcher, "task_queue") else 0,
            }
        elif dispatcher_name == "semaphore":
            # For semaphore dispatcher, show semaphore availability
            if hasattr(dispatcher, "semaphore_count"):
                stats["stats"] = {
                    "max_concurrent": dispatcher.semaphore_count,
                }
        
        return DispatcherStatsResponse(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dispatcher stats for '{dispatcher_type}': {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get dispatcher stats: {str(e)}"
        )
