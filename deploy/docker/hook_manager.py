"""
Hook Manager for User-Provided Hook Functions
Handles validation, compilation, and safe execution of user-provided hook code
"""

import ast
import asyncio
import traceback
from typing import Dict, Callable, Optional, Tuple, List, Any
import logging

logger = logging.getLogger(__name__)


class UserHookManager:
    """Manages user-provided hook functions with error isolation"""
    
    # Expected signatures for each hook point
    HOOK_SIGNATURES = {
        "on_browser_created": ["browser"],
        "on_page_context_created": ["page", "context"],
        "before_goto": ["page", "context", "url"],
        "after_goto": ["page", "context", "url", "response"],
        "on_user_agent_updated": ["page", "context", "user_agent"],
        "on_execution_started": ["page", "context"],
        "before_retrieve_html": ["page", "context"],
        "before_return_html": ["page", "context", "html"]
    }
    
    # Default timeout for hook execution (in seconds)
    DEFAULT_TIMEOUT = 30
    
    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.errors: List[Dict[str, Any]] = []
        self.compiled_hooks: Dict[str, Callable] = {}
        self.execution_log: List[Dict[str, Any]] = []
    
    def validate_hook_structure(self, hook_code: str, hook_point: str) -> Tuple[bool, str]:
        """
        Validate the structure of user-provided hook code
        
        Args:
            hook_code: The Python code string containing the hook function
            hook_point: The hook point name (e.g., 'on_page_context_created')
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Parse the code
            tree = ast.parse(hook_code)
            
            # Check if it's empty
            if not tree.body:
                return False, "Hook code is empty"
            
            # Find the function definition
            func_def = None
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_def = node
                    break
            
            if not func_def:
                return False, "Hook must contain a function definition (def or async def)"
            
            # Check if it's async (all hooks should be async)
            if not isinstance(func_def, ast.AsyncFunctionDef):
                return False, f"Hook function must be async (use 'async def' instead of 'def')"
            
            # Get function name for better error messages
            func_name = func_def.name
            
            # Validate parameters
            expected_params = self.HOOK_SIGNATURES.get(hook_point, [])
            if not expected_params:
                return False, f"Unknown hook point: {hook_point}"
            
            func_params = [arg.arg for arg in func_def.args.args]
            
            # Check if it has **kwargs for flexibility
            has_kwargs = func_def.args.kwarg is not None
            
            # Must have at least the expected parameters
            missing_params = []
            for expected in expected_params:
                if expected not in func_params:
                    missing_params.append(expected)
            
            if missing_params and not has_kwargs:
                return False, f"Hook function '{func_name}' must accept parameters: {', '.join(expected_params)} (missing: {', '.join(missing_params)})"
            
            # Check if it returns something (should return page or browser)
            has_return = any(isinstance(node, ast.Return) for node in ast.walk(func_def))
            if not has_return:
                # Warning, not error - we'll handle this
                logger.warning(f"Hook function '{func_name}' should return the {expected_params[0]} object")
            
            return True, "Valid"
            
        except SyntaxError as e:
            return False, f"Syntax error at line {e.lineno}: {str(e)}"
        except Exception as e:
            return False, f"Failed to parse hook code: {str(e)}"
    
    def compile_hook(self, hook_code: str, hook_point: str) -> Optional[Callable]:
        """
        Compile user-provided hook code into a callable function
        
        Args:
            hook_code: The Python code string
            hook_point: The hook point name
            
        Returns:
            Compiled function or None if compilation failed
        """
        try:
            # Create a safe namespace for the hook
            # Use a more complete builtins that includes __import__
            import builtins
            safe_builtins = {}
            
            # Add safe built-in functions
            allowed_builtins = [
                'print', 'len', 'str', 'int', 'float', 'bool',
                'list', 'dict', 'set', 'tuple', 'range', 'enumerate',
                'zip', 'map', 'filter', 'any', 'all', 'sum', 'min', 'max',
                'sorted', 'reversed', 'abs', 'round', 'isinstance', 'type',
                'getattr', 'hasattr', 'setattr', 'callable', 'iter', 'next',
                '__import__', '__build_class__'  # Required for exec
            ]
            
            for name in allowed_builtins:
                if hasattr(builtins, name):
                    safe_builtins[name] = getattr(builtins, name)
            
            namespace = {
                '__name__': f'user_hook_{hook_point}',
                '__builtins__': safe_builtins
            }
            
            # Add commonly needed imports
            exec("import asyncio", namespace)
            exec("import json", namespace)
            exec("import re", namespace)
            exec("from typing import Dict, List, Optional", namespace)
            
            # Execute the code to define the function
            exec(hook_code, namespace)
            
            # Find the async function in the namespace
            for name, obj in namespace.items():
                if callable(obj) and not name.startswith('_') and asyncio.iscoroutinefunction(obj):
                    return obj
            
            # If no async function found, look for any function
            for name, obj in namespace.items():
                if callable(obj) and not name.startswith('_'):
                    logger.warning(f"Found non-async function '{name}' - wrapping it")
                    # Wrap sync function in async
                    async def async_wrapper(*args, **kwargs):
                        return obj(*args, **kwargs)
                    return async_wrapper
            
            raise ValueError("No callable function found in hook code")
            
        except Exception as e:
            error = {
                'hook_point': hook_point,
                'error': f"Failed to compile hook: {str(e)}",
                'type': 'compilation_error',
                'traceback': traceback.format_exc()
            }
            self.errors.append(error)
            logger.error(f"Hook compilation failed for {hook_point}: {str(e)}")
            return None
    
    async def execute_hook_safely(
        self, 
        hook_func: Callable, 
        hook_point: str,
        *args, 
        **kwargs
    ) -> Tuple[Any, Optional[Dict]]:
        """
        Execute a user hook with error isolation and timeout
        
        Args:
            hook_func: The compiled hook function
            hook_point: The hook point name
            *args, **kwargs: Arguments to pass to the hook
            
        Returns:
            Tuple of (result, error_dict)
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Add timeout to prevent infinite loops
            result = await asyncio.wait_for(
                hook_func(*args, **kwargs),
                timeout=self.timeout
            )
            
            # Log successful execution
            execution_time = asyncio.get_event_loop().time() - start_time
            self.execution_log.append({
                'hook_point': hook_point,
                'status': 'success',
                'execution_time': execution_time,
                'timestamp': start_time
            })
            
            return result, None
            
        except asyncio.TimeoutError:
            error = {
                'hook_point': hook_point,
                'error': f'Hook execution timed out ({self.timeout}s limit)',
                'type': 'timeout',
                'execution_time': self.timeout
            }
            self.errors.append(error)
            self.execution_log.append({
                'hook_point': hook_point,
                'status': 'timeout',
                'error': error['error'],
                'execution_time': self.timeout,
                'timestamp': start_time
            })
            # Return the first argument (usually page/browser) to continue
            return args[0] if args else None, error
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            error = {
                'hook_point': hook_point,
                'error': str(e),
                'type': type(e).__name__,
                'traceback': traceback.format_exc(),
                'execution_time': execution_time
            }
            self.errors.append(error)
            self.execution_log.append({
                'hook_point': hook_point,
                'status': 'failed',
                'error': str(e),
                'error_type': type(e).__name__,
                'execution_time': execution_time,
                'timestamp': start_time
            })
            # Return the first argument (usually page/browser) to continue
            return args[0] if args else None, error
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of hook execution"""
        total_hooks = len(self.execution_log)
        successful = sum(1 for log in self.execution_log if log['status'] == 'success')
        failed = sum(1 for log in self.execution_log if log['status'] == 'failed')
        timed_out = sum(1 for log in self.execution_log if log['status'] == 'timeout')
        
        return {
            'total_executions': total_hooks,
            'successful': successful,
            'failed': failed,
            'timed_out': timed_out,
            'success_rate': (successful / total_hooks * 100) if total_hooks > 0 else 0,
            'total_errors': len(self.errors)
        }


class IsolatedHookWrapper:
    """Wraps user hooks with error isolation and reporting"""
    
    def __init__(self, hook_manager: UserHookManager):
        self.hook_manager = hook_manager
    
    def create_hook_wrapper(self, user_hook: Callable, hook_point: str) -> Callable:
        """
        Create a wrapper that isolates hook errors from main process
        
        Args:
            user_hook: The compiled user hook function
            hook_point: The hook point name
            
        Returns:
            Wrapped async function that handles errors gracefully
        """
        
        async def wrapped_hook(*args, **kwargs):
            """Wrapped hook with error isolation"""
            # Get the main return object (page/browser)
            # This ensures we always have something to return
            return_obj = None
            if args:
                return_obj = args[0]
            elif 'page' in kwargs:
                return_obj = kwargs['page']
            elif 'browser' in kwargs:
                return_obj = kwargs['browser']
            
            try:
                # Execute user hook with safety
                result, error = await self.hook_manager.execute_hook_safely(
                    user_hook, 
                    hook_point,
                    *args, 
                    **kwargs
                )
                
                if error:
                    # Hook failed but we continue with original object
                    logger.warning(f"User hook failed at {hook_point}: {error['error']}")
                    return return_obj
                
                # Hook succeeded - return its result or the original object
                if result is None:
                    logger.debug(f"Hook at {hook_point} returned None, using original object")
                    return return_obj
                
                return result
                
            except Exception as e:
                # This should rarely happen due to execute_hook_safely
                logger.error(f"Unexpected error in hook wrapper for {hook_point}: {e}")
                return return_obj
        
        # Set function name for debugging
        wrapped_hook.__name__ = f"wrapped_{hook_point}"
        return wrapped_hook


async def process_user_hooks(
    hooks_input: Dict[str, str],
    timeout: int = 30
) -> Tuple[Dict[str, Callable], List[Dict], UserHookManager]:
    """
    Process and compile user-provided hook functions
    
    Args:
        hooks_input: Dictionary mapping hook points to code strings
        timeout: Timeout for each hook execution
        
    Returns:
        Tuple of (compiled_hooks, validation_errors, hook_manager)
    """
    
    hook_manager = UserHookManager(timeout=timeout)
    wrapper = IsolatedHookWrapper(hook_manager)
    compiled_hooks = {}
    validation_errors = []
    
    for hook_point, hook_code in hooks_input.items():
        # Skip empty hooks
        if not hook_code or not hook_code.strip():
            continue
        
        # Validate hook point
        if hook_point not in UserHookManager.HOOK_SIGNATURES:
            validation_errors.append({
                'hook_point': hook_point,
                'error': f'Unknown hook point. Valid points: {", ".join(UserHookManager.HOOK_SIGNATURES.keys())}',
                'code_preview': hook_code[:100] + '...' if len(hook_code) > 100 else hook_code
            })
            continue
        
        # Validate structure
        is_valid, message = hook_manager.validate_hook_structure(hook_code, hook_point)
        if not is_valid:
            validation_errors.append({
                'hook_point': hook_point,
                'error': message,
                'code_preview': hook_code[:100] + '...' if len(hook_code) > 100 else hook_code
            })
            continue
        
        # Compile the hook
        hook_func = hook_manager.compile_hook(hook_code, hook_point)
        if hook_func:
            # Wrap with error isolation
            wrapped_hook = wrapper.create_hook_wrapper(hook_func, hook_point)
            compiled_hooks[hook_point] = wrapped_hook
            logger.info(f"Successfully compiled hook for {hook_point}")
        else:
            validation_errors.append({
                'hook_point': hook_point,
                'error': 'Failed to compile hook function - check syntax and structure',
                'code_preview': hook_code[:100] + '...' if len(hook_code) > 100 else hook_code
            })
    
    return compiled_hooks, validation_errors, hook_manager


async def process_user_hooks_with_manager(
    hooks_input: Dict[str, str],
    hook_manager: UserHookManager
) -> Tuple[Dict[str, Callable], List[Dict]]:
    """
    Process and compile user-provided hook functions with existing manager
    
    Args:
        hooks_input: Dictionary mapping hook points to code strings
        hook_manager: Existing UserHookManager instance
        
    Returns:
        Tuple of (compiled_hooks, validation_errors)
    """
    
    wrapper = IsolatedHookWrapper(hook_manager)
    compiled_hooks = {}
    validation_errors = []
    
    for hook_point, hook_code in hooks_input.items():
        # Skip empty hooks
        if not hook_code or not hook_code.strip():
            continue
        
        # Validate hook point
        if hook_point not in UserHookManager.HOOK_SIGNATURES:
            validation_errors.append({
                'hook_point': hook_point,
                'error': f'Unknown hook point. Valid points: {", ".join(UserHookManager.HOOK_SIGNATURES.keys())}',
                'code_preview': hook_code[:100] + '...' if len(hook_code) > 100 else hook_code
            })
            continue
        
        # Validate structure
        is_valid, message = hook_manager.validate_hook_structure(hook_code, hook_point)
        if not is_valid:
            validation_errors.append({
                'hook_point': hook_point,
                'error': message,
                'code_preview': hook_code[:100] + '...' if len(hook_code) > 100 else hook_code
            })
            continue
        
        # Compile the hook
        hook_func = hook_manager.compile_hook(hook_code, hook_point)
        if hook_func:
            # Wrap with error isolation
            wrapped_hook = wrapper.create_hook_wrapper(hook_func, hook_point)
            compiled_hooks[hook_point] = wrapped_hook
            logger.info(f"Successfully compiled hook for {hook_point}")
        else:
            validation_errors.append({
                'hook_point': hook_point,
                'error': 'Failed to compile hook function - check syntax and structure',
                'code_preview': hook_code[:100] + '...' if len(hook_code) > 100 else hook_code
            })
    
    return compiled_hooks, validation_errors


async def attach_user_hooks_to_crawler(
    crawler,  # AsyncWebCrawler instance
    user_hooks: Dict[str, str],
    timeout: int = 30,
    hook_manager: Optional[UserHookManager] = None
) -> Tuple[Dict[str, Any], UserHookManager]:
    """
    Attach user-provided hooks to crawler with full error reporting
    
    Args:
        crawler: AsyncWebCrawler instance
        user_hooks: Dictionary mapping hook points to code strings
        timeout: Timeout for each hook execution
        hook_manager: Optional existing UserHookManager instance
        
    Returns:
        Tuple of (status_dict, hook_manager)
    """
    
    # Use provided hook_manager or create a new one
    if hook_manager is None:
        hook_manager = UserHookManager(timeout=timeout)
    
    # Process hooks with the hook_manager
    compiled_hooks, validation_errors = await process_user_hooks_with_manager(
        user_hooks, hook_manager
    )
    
    # Log validation errors
    if validation_errors:
        logger.warning(f"Hook validation errors: {validation_errors}")
    
    # Attach successfully compiled hooks
    attached_hooks = []
    for hook_point, wrapped_hook in compiled_hooks.items():
        try:
            crawler.crawler_strategy.set_hook(hook_point, wrapped_hook)
            attached_hooks.append(hook_point)
            logger.info(f"Attached hook to {hook_point}")
        except Exception as e:
            logger.error(f"Failed to attach hook to {hook_point}: {e}")
            validation_errors.append({
                'hook_point': hook_point,
                'error': f'Failed to attach hook: {str(e)}'
            })
    
    status = 'success' if not validation_errors else ('partial' if attached_hooks else 'failed')
    
    status_dict = {
        'status': status,
        'attached_hooks': attached_hooks,
        'validation_errors': validation_errors,
        'total_hooks_provided': len(user_hooks),
        'successfully_attached': len(attached_hooks),
        'failed_validation': len(validation_errors)
    }
    
    return status_dict, hook_manager