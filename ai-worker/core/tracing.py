"""
Tracing, Telemetry, Timing, and Decision Logging
Provides observability for debugging and performance analysis
"""

import logging
import time
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass, field
from contextlib import contextmanager
import functools
import json
from pathlib import Path

from core.paths import get_logs_dir

logger = logging.getLogger(__name__)


@dataclass
class Trace:
    """Execution trace"""
    trace_id: str
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    status: str = "running"  # "running", "success", "error"
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    parent_trace_id: Optional[str] = None
    children: List[str] = field(default_factory=list)


class Tracer:
    """
    Tracing and telemetry system
    Tracks execution timing, decisions, and performance metrics
    """
    
    def __init__(self, enable_file_logging: bool = True):
        """
        Initialize tracer
        
        Args:
            enable_file_logging: Write traces to file
        """
        self.traces: Dict[str, Trace] = {}
        self.enable_file_logging = enable_file_logging
        self.trace_file = get_logs_dir() / "traces.jsonl" if enable_file_logging else None
        self._trace_counter = 0
        
        logger.info("Tracer initialized")
    
    def _generate_trace_id(self) -> str:
        """Generate unique trace ID"""
        self._trace_counter += 1
        timestamp = int(time.time() * 1000)
        return f"trace_{timestamp}_{self._trace_counter}"
    
    def start_trace(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
        parent_trace_id: Optional[str] = None
    ) -> str:
        """
        Start new trace
        
        Args:
            name: Trace name
            metadata: Additional metadata
            parent_trace_id: Parent trace ID for nested traces
        
        Returns:
            Trace ID
        """
        trace_id = self._generate_trace_id()
        
        trace = Trace(
            trace_id=trace_id,
            name=name,
            start_time=time.time(),
            metadata=metadata or {},
            parent_trace_id=parent_trace_id
        )
        
        self.traces[trace_id] = trace
        
        # Add to parent's children
        if parent_trace_id and parent_trace_id in self.traces:
            self.traces[parent_trace_id].children.append(trace_id)
        
        logger.debug(f"Trace started: {name} ({trace_id})")
        
        return trace_id
    
    def end_trace(
        self,
        trace_id: str,
        status: str = "success",
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        End trace
        
        Args:
            trace_id: Trace identifier
            status: "success" or "error"
            error: Error message if failed
            metadata: Additional metadata to merge
        """
        if trace_id not in self.traces:
            logger.warning(f"Trace not found: {trace_id}")
            return
        
        trace = self.traces[trace_id]
        trace.end_time = time.time()
        trace.duration_ms = (trace.end_time - trace.start_time) * 1000
        trace.status = status
        trace.error = error
        
        if metadata:
            trace.metadata.update(metadata)
        
        logger.debug(f"Trace ended: {trace.name} ({trace_id}) - {trace.duration_ms:.2f}ms")
        
        # Write to file
        if self.enable_file_logging:
            self._write_trace_to_file(trace)
    
    def _write_trace_to_file(self, trace: Trace):
        """Write trace to JSONL file"""
        try:
            trace_data = {
                "trace_id": trace.trace_id,
                "name": trace.name,
                "start_time": datetime.fromtimestamp(trace.start_time).isoformat(),
                "end_time": datetime.fromtimestamp(trace.end_time).isoformat() if trace.end_time else None,
                "duration_ms": trace.duration_ms,
                "status": trace.status,
                "metadata": trace.metadata,
                "error": trace.error,
                "parent_trace_id": trace.parent_trace_id
            }
            
            with open(self.trace_file, 'a') as f:
                f.write(json.dumps(trace_data) + '\n')
        
        except Exception as e:
            logger.error(f"Failed to write trace to file: {e}")
    
    @contextmanager
    def trace(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
        parent_trace_id: Optional[str] = None
    ):
        """
        Context manager for tracing
        
        Args:
            name: Trace name
            metadata: Additional metadata
            parent_trace_id: Parent trace ID
        
        Example:
            with tracer.trace("my_operation"):
                do_something()
        """
        trace_id = self.start_trace(name, metadata, parent_trace_id)
        
        try:
            yield trace_id
            self.end_trace(trace_id, status="success")
        except Exception as e:
            self.end_trace(trace_id, status="error", error=str(e))
            raise
    
    def trace_function(
        self,
        name: Optional[str] = None,
        include_args: bool = False
    ):
        """
        Decorator for tracing functions
        
        Args:
            name: Trace name (defaults to function name)
            include_args: Include function arguments in metadata
        
        Example:
            @tracer.trace_function()
            def my_function(x, y):
                return x + y
        """
        def decorator(func: Callable) -> Callable:
            trace_name = name or func.__name__
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                metadata = {}
                if include_args:
                    metadata["args"] = str(args)
                    metadata["kwargs"] = str(kwargs)
                
                with self.trace(trace_name, metadata):
                    return func(*args, **kwargs)
            
            return wrapper
        
        return decorator
    
    def log_decision(
        self,
        decision_name: str,
        chosen_option: str,
        options: List[str],
        reasoning: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log AI decision for debugging
        
        Args:
            decision_name: Name of decision
            chosen_option: Selected option
            options: All available options
            reasoning: Why this option was chosen
            metadata: Additional context
        """
        decision_data = {
            "timestamp": datetime.now().isoformat(),
            "decision": decision_name,
            "chosen": chosen_option,
            "options": options,
            "reasoning": reasoning,
            "metadata": metadata or {}
        }
        
        logger.info(f"Decision: {decision_name} -> {chosen_option} ({reasoning})")
        
        # Write to decisions log
        if self.enable_file_logging:
            decisions_file = get_logs_dir() / "decisions.jsonl"
            with open(decisions_file, 'a') as f:
                f.write(json.dumps(decision_data) + '\n')
    
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get trace by ID"""
        return self.traces.get(trace_id)
    
    def get_trace_tree(self, trace_id: str) -> Dict[str, Any]:
        """
        Get trace with all children (tree structure)
        
        Args:
            trace_id: Root trace ID
        
        Returns:
            Nested trace dictionary
        """
        trace = self.get_trace(trace_id)
        if not trace:
            return {}
        
        tree = {
            "trace_id": trace.trace_id,
            "name": trace.name,
            "duration_ms": trace.duration_ms,
            "status": trace.status,
            "metadata": trace.metadata,
            "children": []
        }
        
        for child_id in trace.children:
            child_tree = self.get_trace_tree(child_id)
            if child_tree:
                tree["children"].append(child_tree)
        
        return tree
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tracing statistics"""
        total_traces = len(self.traces)
        completed = sum(1 for t in self.traces.values() if t.end_time is not None)
        successful = sum(1 for t in self.traces.values() if t.status == "success")
        failed = sum(1 for t in self.traces.values() if t.status == "error")
        
        # Average duration
        durations = [t.duration_ms for t in self.traces.values() if t.duration_ms is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "total_traces": total_traces,
            "completed": completed,
            "successful": successful,
            "failed": failed,
            "avg_duration_ms": avg_duration
        }
    
    def cleanup_old_traces(self, max_traces: int = 1000):
        """
        Remove old traces to prevent memory bloat
        
        Args:
            max_traces: Maximum number of traces to keep
        """
        if len(self.traces) <= max_traces:
            return
        
        # Sort by start time and keep most recent
        sorted_traces = sorted(
            self.traces.items(),
            key=lambda x: x[1].start_time,
            reverse=True
        )
        
        self.traces = dict(sorted_traces[:max_traces])
        logger.info(f"Cleaned up old traces, kept {max_traces}")


# Global tracer instance
_global_tracer: Optional[Tracer] = None


def get_tracer() -> Tracer:
    """Get global tracer instance"""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = Tracer()
    return _global_tracer


if __name__ == "__main__":
    # Test tracer
    print("Testing Tracer")
    print("=" * 50)
    
    tracer = Tracer(enable_file_logging=False)
    
    # Test context manager
    with tracer.trace("test_operation", metadata={"user": "test"}):
        time.sleep(0.1)
    
    # Test decorator
    @tracer.trace_function(include_args=True)
    def test_function(x, y):
        time.sleep(0.05)
        return x + y
    
    result = test_function(5, 10)
    print(f"Result: {result}")
    
    # Test decision logging
    tracer.log_decision(
        decision_name="model_selection",
        chosen_option="phi-3-mini",
        options=["phi-3-mini", "mistral-7b"],
        reasoning="Insufficient RAM for larger model"
    )
    
    # Test stats
    stats = tracer.get_stats()
    print(f"\nStats: {stats}")
    
    print("=" * 50)
