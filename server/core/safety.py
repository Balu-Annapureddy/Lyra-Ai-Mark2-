"""
Safety Layer - Timeouts, Memory Limits, and Auto-Kill
Prevents system crashes by wrapping all model operations
"""

import asyncio
import functools
import psutil
import signal
import logging
from typing import Callable, Any, Optional
from contextlib import contextmanager
import threading

logger = logging.getLogger(__name__)


class SafetyViolation(Exception):
    """Raised when a safety limit is violated"""
    pass


class TimeoutError(SafetyViolation):
    """Raised when operation exceeds timeout"""
    pass


class MemoryLimitError(SafetyViolation):
    """Raised when memory limit is exceeded"""
    pass


# Default safety limits
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_MEMORY_LIMIT_GB = 6.0  # For 8GB systems, leave 2GB for OS


def with_timeout(seconds: int = DEFAULT_TIMEOUT_SECONDS):
    """
    Decorator to add timeout to synchronous functions
    
    Args:
        seconds: Timeout in seconds
    
    Raises:
        TimeoutError: If function exceeds timeout
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = [None]
            exception = [None]
            
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=target, daemon=True)
            thread.start()
            thread.join(timeout=seconds)
            
            if thread.is_alive():
                logger.error(f"{func.__name__} exceeded timeout of {seconds}s")
                raise TimeoutError(f"{func.__name__} exceeded {seconds}s timeout")
            
            if exception[0]:
                raise exception[0]
            
            return result[0]
        
        return wrapper
    return decorator


def with_async_timeout(seconds: int = DEFAULT_TIMEOUT_SECONDS):
    """
    Decorator to add timeout to async functions
    
    Args:
        seconds: Timeout in seconds
    
    Raises:
        TimeoutError: If function exceeds timeout
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=seconds
                )
            except asyncio.TimeoutError:
                logger.error(f"{func.__name__} exceeded timeout of {seconds}s")
                raise TimeoutError(f"{func.__name__} exceeded {seconds}s timeout")
        
        return wrapper
    return decorator


def check_memory_limit(limit_gb: float = DEFAULT_MEMORY_LIMIT_GB):
    """
    Check if current memory usage exceeds limit
    
    Args:
        limit_gb: Memory limit in GB
    
    Raises:
        MemoryLimitError: If memory usage exceeds limit
    """
    mem = psutil.virtual_memory()
    used_gb = mem.used / (1024 ** 3)
    
    if used_gb > limit_gb:
        logger.error(
            f"Memory limit exceeded: {used_gb:.1f}GB > {limit_gb:.1f}GB"
        )
        raise MemoryLimitError(
            f"Memory usage {used_gb:.1f}GB exceeds limit {limit_gb:.1f}GB"
        )


def with_memory_limit(limit_gb: float = DEFAULT_MEMORY_LIMIT_GB):
    """
    Decorator to enforce memory limit before function execution
    
    Args:
        limit_gb: Memory limit in GB
    
    Raises:
        MemoryLimitError: If memory usage exceeds limit
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            check_memory_limit(limit_gb)
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


@contextmanager
def safe_execution(
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    memory_limit_gb: float = DEFAULT_MEMORY_LIMIT_GB,
    operation_name: str = "operation"
):
    """
    Context manager for safe execution with timeout and memory checks
    
    Args:
        timeout_seconds: Timeout in seconds
        memory_limit_gb: Memory limit in GB
        operation_name: Name of operation (for logging)
    
    Example:
        with safe_execution(timeout_seconds=10, operation_name="model_load"):
            model.load()
    """
    logger.info(f"Starting safe execution: {operation_name}")
    
    # Check memory before starting
    check_memory_limit(memory_limit_gb)
    
    start_time = asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0
    
    try:
        yield
    except Exception as e:
        logger.error(f"Error in {operation_name}: {e}")
        raise
    finally:
        if start_time:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout_seconds:
                logger.warning(
                    f"{operation_name} took {elapsed:.1f}s "
                    f"(timeout: {timeout_seconds}s)"
                )


def safe_model_operation(
    func: Callable,
    timeout: int = 30,
    memory_limit: float = DEFAULT_MEMORY_LIMIT_GB,
    operation_name: Optional[str] = None
) -> Any:
    """
    Safely execute a model operation with all safety checks
    
    Args:
        func: Function to execute
        timeout: Timeout in seconds
        memory_limit: Memory limit in GB
        operation_name: Name of operation
    
    Returns:
        Result of function execution
    
    Raises:
        SafetyViolation: If any safety limit is violated
    """
    op_name = operation_name or func.__name__
    
    logger.info(f"Executing safe model operation: {op_name}")
    
    # Pre-execution checks
    check_memory_limit(memory_limit)
    
    # Execute with timeout
    try:
        if asyncio.iscoroutinefunction(func):
            # Async function
            return asyncio.run(
                asyncio.wait_for(func(), timeout=timeout)
            )
        else:
            # Sync function
            @with_timeout(timeout)
            def wrapped():
                return func()
            
            return wrapped()
    
    except Exception as e:
        logger.error(f"Safe model operation failed: {op_name} - {e}")
        raise


def force_garbage_collection():
    """Force Python garbage collection to free memory"""
    import gc
    gc.collect()
    logger.debug("Forced garbage collection")


def kill_process_if_frozen(pid: int, timeout: int = 10):
    """
    Kill a process if it's frozen/unresponsive
    
    Args:
        pid: Process ID
        timeout: Timeout in seconds
    """
    try:
        process = psutil.Process(pid)
        process.wait(timeout=timeout)
    except psutil.TimeoutExpired:
        logger.warning(f"Process {pid} frozen, killing...")
        try:
            process.kill()
            logger.info(f"Process {pid} killed successfully")
        except Exception as e:
            logger.error(f"Failed to kill process {pid}: {e}")


if __name__ == "__main__":
    # Test safety layer
    import time
    
    print("Testing Safety Layer")
    print("=" * 50)
    
    # Test timeout
    @with_timeout(2)
    def slow_function():
        time.sleep(5)
        return "Done"
    
    try:
        result = slow_function()
        print(f"Result: {result}")
    except TimeoutError as e:
        print(f"✓ Timeout caught: {e}")
    
    # Test memory limit
    try:
        check_memory_limit(limit_gb=0.1)  # Very low limit
    except MemoryLimitError as e:
        print(f"✓ Memory limit caught: {e}")
    
    # Test safe execution
    with safe_execution(timeout_seconds=5, operation_name="test"):
        print("✓ Safe execution works")
    
    print("=" * 50)
    print("Safety layer tests complete!")
