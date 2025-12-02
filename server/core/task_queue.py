"""
Task Priority Queue
Prioritizes tasks with backpressure management and starvation prevention
"""

import time
import heapq
import threading
from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass, field
from enum import IntEnum
from datetime import datetime

from core.structured_logger import get_structured_logger
from core.metrics_manager import get_metrics_manager

class Priority(IntEnum):
    CRITICAL = 0  # Voice
    HIGH = 1      # Chat
    NORMAL = 2    # Analysis
    LOW = 3       # Indexing

@dataclass(order=True)
class TaskItem:
    priority: int
    timestamp: float
    task_id: str = field(compare=False)
    func: Callable = field(compare=False)
    args: Tuple = field(compare=False)
    kwargs: Dict = field(compare=False)
    created_at: float = field(compare=False, default_factory=time.time)

class TaskQueue:
    """
    Priority queue for task execution.
    
    Features:
    - Priority Levels: CRITICAL, HIGH, NORMAL, LOW
    - Starvation Prevention: Age boosting for low priority tasks
    - Backpressure: Reject/spill policies on overload
    """
    
    def __init__(self, max_size: int = 1000, starvation_threshold_sec: float = 60.0):
        self.struct_logger = get_structured_logger("TaskQueue")
        self.metrics = get_metrics_manager()
        self.max_size = max_size
        self.starvation_threshold = starvation_threshold_sec
        
        self._queue: List[TaskItem] = []
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        
        self.struct_logger.info(
            "initialized",
            "Task queue initialized",
            max_size=max_size,
            starvation_threshold=starvation_threshold_sec
        )

    def submit(self, priority: Priority, task_id: str, func: Callable, *args, **kwargs) -> bool:
        """
        Submit a task to the queue
        
        Args:
            priority: Task priority
            task_id: Unique ID
            func: Function to execute
            
        Returns:
            True if accepted, False if rejected (backpressure)
        """
        with self._lock:
            # Backpressure check
            if len(self._queue) >= self.max_size:
                # Reject LOW/NORMAL if full, allow CRITICAL if we can spill or force
                if priority > Priority.HIGH:
                    self.struct_logger.warning("backpressure_reject", f"Queue full, rejecting {priority.name} task {task_id}")
                    self.metrics.increment_counter("task_rejected", 1, {"priority": priority.name})
                    return False
                
                # For CRITICAL/HIGH, we might want to spill to disk or drop lowest priority
                # Simplified: Drop lowest priority task to make room
                if self._drop_lowest_priority():
                    self.struct_logger.info("backpressure_drop", f"Dropped low priority task for {task_id}")
                else:
                    self.struct_logger.error("backpressure_fail", f"Queue full of high priority tasks, rejecting {task_id}")
                    return False

            item = TaskItem(
                priority=int(priority),
                timestamp=time.time(),
                task_id=task_id,
                func=func,
                args=args,
                kwargs=kwargs
            )
            
            heapq.heappush(self._queue, item)
            self._condition.notify()
            
            self.metrics.increment_counter("task_submitted", 1, {"priority": priority.name})
            return True

    def _drop_lowest_priority(self) -> bool:
        """Drop the lowest priority task to make room. Assumes lock held."""
        if not self._queue:
            return False
            
        # Find lowest priority (highest number)
        # heapq is a min-heap based on (priority, timestamp)
        # We need to scan to find max priority (lowest importance)
        
        # This is O(N), but queue size is bounded
        lowest_idx = -1
        lowest_prio = -1
        
        for i, item in enumerate(self._queue):
            if item.priority > lowest_prio:
                lowest_prio = item.priority
                lowest_idx = i
            elif item.priority == lowest_prio:
                # If same priority, drop newer one (LIFO drop for same priority?) 
                # Or older? Usually drop newest to keep older progress? 
                # Let's drop newest of lowest priority.
                if item.timestamp > self._queue[lowest_idx].timestamp:
                    lowest_idx = i
                    
        if lowest_idx != -1 and lowest_prio > Priority.HIGH: # Only drop NORMAL/LOW
            del self._queue[lowest_idx]
            heapq.heapify(self._queue) # Re-heapify O(N)
            return True
            
        return False

    def get_next_task(self, timeout: Optional[float] = None) -> Optional[TaskItem]:
        """
        Get next task to execute
        
        Args:
            timeout: Wait timeout
            
        Returns:
            TaskItem or None
        """
        with self._condition:
            # Wait if empty
            if not self._queue:
                self._condition.wait(timeout)
                if not self._queue:
                    return None
            
            # Starvation Check: Boost priority of old tasks
            self._handle_starvation()
            
            # Pop highest priority
            item = heapq.heappop(self._queue)
            
            # Record wait time
            wait_time = time.time() - item.created_at
            self.metrics.record_time("task_wait_time", wait_time, {"priority": Priority(item.priority).name})
            
            return item

    def _handle_starvation(self):
        """Boost priority of starving tasks. Assumes lock held."""
        now = time.time()
        changed = False
        
        for item in self._queue:
            if item.priority > Priority.HIGH: # Only boost NORMAL/LOW
                age = now - item.created_at
                if age > self.starvation_threshold:
                    # Boost to HIGH
                    item.priority = int(Priority.HIGH)
                    # Reset timestamp to maintain FIFO within new priority? 
                    # Or keep original to be processed first in HIGH?
                    # Keep original timestamp is better.
                    changed = True
                    self.struct_logger.info("starvation_boost", f"Boosted task {item.task_id} to HIGH")
                    
        if changed:
            heapq.heapify(self._queue)

    def qsize(self) -> int:
        with self._lock:
            return len(self._queue)

# Singleton
_task_queue: Optional[TaskQueue] = None

def get_task_queue() -> TaskQueue:
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue()
    return _task_queue
