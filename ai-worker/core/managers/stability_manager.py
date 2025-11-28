"""
Stability Manager
Manages backend stability with error handling, retry logic, and graceful degradation
"""

import logging
import time
from typing import Optional, Callable, Any, Dict, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from functools import wraps

from core.structured_logger import get_structured_logger


@dataclass
class ErrorRecord:
    """Record of an error occurrence"""
    timestamp: datetime
    error_type: str
    error_message: str
    context: Dict[str, Any]
    retries: int = 0


class StabilityManager:
    """
    Manages backend stability with error handling and recovery
    
    Features:
    - Safe model loading with try/except wrappers
    - Automatic retry with exponential backoff
    - Graceful degradation on failures
    - Error tracking and reporting
    """
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        """
        Initialize stability manager
        
        Args:
            max_retries: Maximum number of retries
            base_delay: Base delay for exponential backoff (seconds)
        """
        self.struct_logger = get_structured_logger("StabilityManager")
        self.max_retries = max_retries
        self.base_delay = base_delay
        
        self._error_history: List[ErrorRecord] = []
        self._max_history = 100
        
        self.struct_logger.info(
            "initialized",
            "Stability manager initialized",
            max_retries=max_retries,
            base_delay=base_delay
        )
    
    def safe_execute(
        self,
        func: Callable,
        *args,
        fallback: Optional[Callable] = None,
        context: Optional[Dict] = None,
        **kwargs
    ) -> Any:
        """
        Execute function with error handling and retry logic
        
        Args:
            func: Function to execute
            *args: Positional arguments for func
            fallback: Optional fallback function if all retries fail
            context: Optional context for error tracking
            **kwargs: Keyword arguments for func
            
        Returns:
            Result from func or fallback
        """
        retries = 0
        last_error = None
        
        while retries <= self.max_retries:
            try:
                result = func(*args, **kwargs)
                
                if retries > 0:
                    self.struct_logger.info(
                        "retry_success",
                        f"Function succeeded after {retries} retries",
                        function=func.__name__,
                        retries=retries
                    )
                
                return result
                
            except Exception as e:
                last_error = e
                retries += 1
                
                # Track error
                self._track_error(e, func.__name__, context or {}, retries)
                
                if retries <= self.max_retries:
                    # Calculate backoff delay
                    delay = self.base_delay * (2 ** (retries - 1))
                    
                    self.struct_logger.warning(
                        "retry_attempt",
                        f"Retry {retries}/{self.max_retries} after {delay}s",
                        function=func.__name__,
                        retry=retries,
                        delay=delay,
                        error=str(e)
                    )
                    
                    time.sleep(delay)
        
        # All retries failed
        self.struct_logger.error(
            "all_retries_failed",
            f"Function failed after {self.max_retries} retries",
            function=func.__name__,
            error=str(last_error)
        )
        
        # Try fallback if provided
        if fallback:
            try:
                self.struct_logger.info(
                    "fallback_attempt",
                    "Attempting fallback function",
                    function=func.__name__,
                    fallback=fallback.__name__
                )
                return fallback(*args, **kwargs)
            except Exception as fb_error:
                self.struct_logger.error(
                    "fallback_failed",
                    f"Fallback also failed: {fb_error}",
                    fallback=fallback.__name__,
                    error=str(fb_error)
                )
        
        # Re-raise last error if no fallback or fallback failed
        raise last_error
    
    def safe_model_load(self, model_id: str, loader_func: Callable) -> Optional[Any]:
        """
        Safely load a model with error handling
        
        Args:
            model_id: Model identifier
            loader_func: Function to load the model
            
        Returns:
            Loaded model or None if failed
        """
        try:
            self.struct_logger.info(
                "model_load_start",
                f"Loading model: {model_id}",
                model_id=model_id
            )
            
            model = self.safe_execute(
                loader_func,
                context={"model_id": model_id, "operation": "model_load"}
            )
            
            self.struct_logger.info(
                "model_load_success",
                f"Model loaded successfully: {model_id}",
                model_id=model_id
            )
            
            return model
            
        except Exception as e:
            self.struct_logger.error(
                "model_load_failed",
                f"Failed to load model {model_id}: {e}",
                model_id=model_id,
                error=str(e)
            )
            return None
    
    def _track_error(
        self,
        error: Exception,
        function_name: str,
        context: Dict[str, Any],
        retries: int
    ):
        """Track an error occurrence"""
        record = ErrorRecord(
            timestamp=datetime.utcnow(),
            error_type=type(error).__name__,
            error_message=str(error),
            context={
                "function": function_name,
                **context
            },
            retries=retries
        )
        
        self._error_history.append(record)
        
        # Trim history if too long
        if len(self._error_history) > self._max_history:
            self._error_history = self._error_history[-self._max_history:]
    
    def get_error_stats(self, since_minutes: int = 60) -> Dict[str, Any]:
        """
        Get error statistics
        
        Args:
            since_minutes: Look back this many minutes
            
        Returns:
            Error statistics dictionary
        """
        cutoff = datetime.utcnow() - timedelta(minutes=since_minutes)
        recent_errors = [e for e in self._error_history if e.timestamp > cutoff]
        
        # Count by error type
        error_counts = {}
        for error in recent_errors:
            error_counts[error.error_type] = error_counts.get(error.error_type, 0) + 1
        
        return {
            "total_errors": len(recent_errors),
            "error_types": error_counts,
            "time_window_minutes": since_minutes,
            "most_recent": recent_errors[-1].__dict__ if recent_errors else None
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Health check for stability manager
        
        Returns:
            Health status dictionary
        """
        recent_stats = self.get_error_stats(since_minutes=5)
        
        # Determine status based on recent errors
        if recent_stats["total_errors"] == 0:
            status = "ok"
        elif recent_stats["total_errors"] < 5:
            status = "degraded"
        else:
            status = "error"
        
        return {
            "status": status,
            "component": "StabilityManager",
            "details": {
                "recent_errors_5min": recent_stats["total_errors"],
                "error_types": recent_stats["error_types"],
                "max_retries": self.max_retries
            },
            "errors": [recent_stats["most_recent"]] if recent_stats["most_recent"] else [],
            "last_check": datetime.utcnow().isoformat()
        }


# Singleton instance
_stability_manager: Optional[StabilityManager] = None


def get_stability_manager() -> StabilityManager:
    """Get or create the global stability manager"""
    global _stability_manager
    if _stability_manager is None:
        _stability_manager = StabilityManager()
    return _stability_manager
