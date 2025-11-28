"""
Metrics Manager
Comprehensive telemetry and metrics tracking
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import threading
from collections import deque

from core.structured_logger import get_structured_logger

@dataclass
class MetricPoint:
    name: str
    value: float
    tags: Dict[str, str]
    timestamp: float = field(default_factory=time.time)

class MetricsManager:
    """
    Centralized metrics collection and reporting
    
    Features:
    - Track counters, gauges, and histograms (timers)
    - Tagging support for granular analysis
    - In-memory storage with optional export (placeholder)
    """
    
    def __init__(self, max_history: int = 1000):
        self.struct_logger = get_structured_logger("MetricsManager")
        self._metrics: deque = deque(maxlen=max_history)
        self._lock = threading.Lock()
        
        # Aggregated stats
        self._counters: Dict[str, float] = {}
        
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Record a generic metric point
        
        Args:
            name: Metric name
            value: Metric value
            tags: Optional tags (e.g., {'model_id': 'llama3'})
        """
        tags = tags or {}
        point = MetricPoint(name, value, tags)
        
        with self._lock:
            self._metrics.append(point)
            
        # Log significant events or errors
        if "error" in name or "failure" in name:
             self.struct_logger.warning(
                 "metric_alert",
                 f"Metric alert: {name}={value}",
                 value=value,
                 tags=tags
             )

    def increment_counter(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        tags = tags or {}
        tag_key = self._get_tag_key(name, tags)
        
        with self._lock:
            current = self._counters.get(tag_key, 0.0)
            self._counters[tag_key] = current + value
            
        self.record_metric(name, value, tags)

    def record_time(self, name: str, duration_seconds: float, tags: Optional[Dict[str, str]] = None):
        """Record a duration"""
        self.record_metric(name, duration_seconds, tags)

    def _get_tag_key(self, name: str, tags: Dict[str, str]) -> str:
        """Generate unique key for counter aggregation"""
        sorted_tags = sorted(tags.items())
        tag_str = ",".join([f"{k}={v}" for k, v in sorted_tags])
        return f"{name}|{tag_str}"

    def get_metrics(self, name_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve recent metrics
        
        Args:
            name_filter: Optional filter by metric name
            
        Returns:
            List of metric dictionaries
        """
        with self._lock:
            data = list(self._metrics)
            
        results = []
        for m in data:
            if name_filter and name_filter not in m.name:
                continue
            results.append({
                "name": m.name,
                "value": m.value,
                "tags": m.tags,
                "timestamp": datetime.fromtimestamp(m.timestamp).isoformat()
            })
        return results

    def get_counter_value(self, name: str, tags: Optional[Dict[str, str]] = None) -> float:
        """Get current value of a counter"""
        tags = tags or {}
        tag_key = self._get_tag_key(name, tags)
        with self._lock:
            return self._counters.get(tag_key, 0.0)

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregated statistics"""
        with self._lock:
            stats = {}
            for key, value in self._counters.items():
                name = key.split("|")[0]
                if name not in stats:
                    stats[name] = {"count": 0.0}
                stats[name]["count"] += value
            return stats

# Singleton
_metrics_manager: Optional[MetricsManager] = None

def get_metrics_manager() -> MetricsManager:
    global _metrics_manager
    if _metrics_manager is None:
        _metrics_manager = MetricsManager()
    return _metrics_manager
