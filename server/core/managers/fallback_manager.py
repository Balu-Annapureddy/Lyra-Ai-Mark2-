"""
Fallback Manager
Handles automatic degradation with circuit breakers and quota tracking
"""

import time
import random
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime
import threading

from core.structured_logger import get_structured_logger
from core.metrics_manager import get_metrics_manager

@dataclass
class CircuitState:
    failures: int
    last_failure_time: float
    is_open: bool
    open_until: float

class FallbackManager:
    """
    Manages fallback chains and circuit breakers.
    
    Features:
    - Circuit Breakers: Per-model failure counting and cool-down.
    - Exponential Backoff: For retries.
    - Quota Tracking: (Placeholder) Track cloud usage.
    """
    
    def __init__(
        self, 
        failure_threshold: int = 5, 
        cooldown_seconds: float = 300.0,
        reset_interval_seconds: float = 60.0
    ):
        self.struct_logger = get_structured_logger("FallbackManager")
        self.metrics = get_metrics_manager()
        
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.reset_interval = reset_interval_seconds
        
        self._circuits: Dict[str, CircuitState] = {}
        self._lock = threading.Lock()
        
        self.struct_logger.info(
            "initialized",
            "Fallback manager initialized",
            threshold=failure_threshold,
            cooldown=cooldown_seconds
        )

    def execute_with_fallback(
        self, 
        func: Callable, 
        model_chain: List[str], 
        *args, 
        **kwargs
    ) -> Any:
        """
        Execute a function using a chain of models for fallback.
        
        Args:
            func: Function to execute, must accept 'model_id' as kwarg
            model_chain: List of model IDs to try in order
            
        Returns:
            Result of function
        """
        last_error = None
        
        for i, model_id in enumerate(model_chain):
            # Check circuit breaker
            if self._is_circuit_open(model_id):
                self.struct_logger.warning("circuit_open", f"Skipping {model_id}, circuit open")
                continue
                
            try:
                # Attempt execution
                start_time = time.time()
                result = func(*args, model_id=model_id, **kwargs)
                
                # Success
                self._record_success(model_id)
                
                if i > 0:
                    self.struct_logger.info(
                        "fallback_success", 
                        f"Fallback succeeded with {model_id}",
                        primary=model_chain[0],
                        fallback=model_id
                    )
                    self.metrics.increment_counter("fallback_success", 1, {"model_id": model_id})
                
                return result
                
            except Exception as e:
                last_error = e
                self.struct_logger.warning(
                    "execution_failed", 
                    f"Failed with {model_id}: {e}",
                    model_id=model_id
                )
                self._record_failure(model_id)
                self.metrics.increment_counter("model_failure", 1, {"model_id": model_id, "error": str(type(e).__name__)})
                
                # Exponential backoff if retrying same model (not implemented here as we switch models)
                # But if we were retrying, we'd sleep here.
                
        # All failed
        self.struct_logger.error("all_fallbacks_failed", "All models in chain failed", chain=model_chain)
        raise last_error

    def _get_circuit(self, model_id: str) -> CircuitState:
        if model_id not in self._circuits:
            self._circuits[model_id] = CircuitState(0, 0, False, 0)
        return self._circuits[model_id]

    def _is_circuit_open(self, model_id: str) -> bool:
        with self._lock:
            circuit = self._get_circuit(model_id)
            if circuit.is_open:
                if time.time() > circuit.open_until:
                    # Half-open / Reset
                    circuit.is_open = False
                    circuit.failures = 0
                    self.struct_logger.info("circuit_reset", f"Circuit cooldown ended for {model_id}")
                    return False
                return True
            return False

    def _record_failure(self, model_id: str):
        with self._lock:
            circuit = self._get_circuit(model_id)
            now = time.time()
            
            # Reset count if interval passed
            if now - circuit.last_failure_time > self.reset_interval:
                circuit.failures = 0
                
            circuit.failures += 1
            circuit.last_failure_time = now
            
            if circuit.failures >= self.failure_threshold:
                circuit.is_open = True
                circuit.open_until = now + self.cooldown_seconds
                self.struct_logger.warning(
                    "circuit_tripped", 
                    f"Circuit tripped for {model_id}",
                    failures=circuit.failures,
                    cooldown=self.cooldown_seconds
                )
                self.metrics.increment_counter("circuit_trip", 1, {"model_id": model_id})

    def _record_success(self, model_id: str):
        with self._lock:
            circuit = self._get_circuit(model_id)
            if circuit.failures > 0:
                circuit.failures = max(0, circuit.failures - 1) # Decay failures on success

# Singleton
_fallback_manager: Optional[FallbackManager] = None

def get_fallback_manager() -> FallbackManager:
    global _fallback_manager
    if _fallback_manager is None:
        _fallback_manager = FallbackManager()
    return _fallback_manager
