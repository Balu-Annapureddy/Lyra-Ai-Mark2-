"""
Event Bus - Async Event System for Module Communication
Enables decoupled communication between subsystems
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Callable, Coroutine
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """System event types"""
    # Model events
    MODEL_LOADED = "model_loaded"
    MODEL_UNLOADED = "model_unloaded"
    MODEL_FAILED = "model_failed"
    
    # GPU events
    GPU_WARNING = "gpu_warning"
    GPU_ERROR = "gpu_error"
    GPU_MEMORY_LOW = "gpu_memory_low"
    
    # Skill events
    SKILL_STARTED = "skill_started"
    SKILL_COMPLETED = "skill_completed"
    SKILL_FAILED = "skill_failed"
    SKILL_TIMEOUT = "skill_timeout"
    
    # System events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    MEMORY_WARNING = "memory_warning"
    MEMORY_CRITICAL = "memory_critical"
    
    # Job events
    JOB_SUBMITTED = "job_submitted"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    
    # Trace events
    NEW_TRACE = "new_trace"
    TRACE_COMPLETED = "trace_completed"
    
    # State events
    STATE_CHANGED = "state_changed"
    CONFIG_CHANGED = "config_changed"


@dataclass
class Event:
    """Event data structure"""
    type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    source: str


class EventBus:
    """
    Async event bus for inter-module communication
    Supports pub/sub pattern with async handlers
    """
    
    def __init__(self):
        """Initialize event bus"""
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._lock = threading.Lock()
        self._event_history: List[Event] = []
        self._max_history = 1000
        
        logger.info("EventBus initialized")
    
    def subscribe(
        self,
        event_type: EventType,
        handler: Callable[[Event], None]
    ):
        """
        Subscribe to event type
        
        Args:
            event_type: Type of event to subscribe to
            handler: Callback function (can be sync or async)
        """
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            
            self._subscribers[event_type].append(handler)
        
        logger.debug(f"Subscribed to {event_type}: {handler.__name__}")
    
    def unsubscribe(
        self,
        event_type: EventType,
        handler: Callable[[Event], None]
    ):
        """
        Unsubscribe from event type
        
        Args:
            event_type: Type of event
            handler: Handler to remove
        """
        with self._lock:
            if event_type in self._subscribers:
                if handler in self._subscribers[event_type]:
                    self._subscribers[event_type].remove(handler)
        
        logger.debug(f"Unsubscribed from {event_type}: {handler.__name__}")
    
    async def publish(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        source: str = "unknown"
    ):
        """
        Publish event to all subscribers
        
        Args:
            event_type: Type of event
            data: Event data
            source: Source module name
        """
        event = Event(
            type=event_type,
            timestamp=datetime.now(),
            data=data,
            source=source
        )
        
        # Add to history
        with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history = self._event_history[-self._max_history:]
            
            # Get subscribers
            handlers = self._subscribers.get(event_type, []).copy()
        
        logger.debug(f"Publishing {event_type} from {source} to {len(handlers)} subscribers")
        
        # Call handlers
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Event handler error ({handler.__name__}): {e}")
    
    def publish_sync(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        source: str = "unknown"
    ):
        """
        Publish event synchronously (for non-async contexts)
        
        Args:
            event_type: Type of event
            data: Event data
            source: Source module name
        """
        event = Event(
            type=event_type,
            timestamp=datetime.now(),
            data=data,
            source=source
        )
        
        # Add to history
        with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history = self._event_history[-self._max_history:]
            
            # Get subscribers (only sync handlers)
            handlers = self._subscribers.get(event_type, []).copy()
        
        logger.debug(f"Publishing {event_type} (sync) from {source}")
        
        # Call only sync handlers
        for handler in handlers:
            if not asyncio.iscoroutinefunction(handler):
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Event handler error ({handler.__name__}): {e}")
    
    def get_history(
        self,
        event_type: Optional[EventType] = None,
        last_n: Optional[int] = None
    ) -> List[Event]:
        """
        Get event history
        
        Args:
            event_type: Filter by event type
            last_n: Return last N events
        
        Returns:
            List of events
        """
        with self._lock:
            events = self._event_history.copy()
        
        # Filter by type
        if event_type:
            events = [e for e in events if e.type == event_type]
        
        # Limit count
        if last_n:
            events = events[-last_n:]
        
        return events
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        with self._lock:
            subscriber_count = sum(len(handlers) for handlers in self._subscribers.values())
            
            # Count events by type
            event_counts = {}
            for event in self._event_history:
                event_counts[event.type] = event_counts.get(event.type, 0) + 1
        
        return {
            "total_subscribers": subscriber_count,
            "event_types": len(self._subscribers),
            "history_size": len(self._event_history),
            "event_counts": event_counts
        }
    
    def clear_history(self):
        """Clear event history"""
        with self._lock:
            self._event_history.clear()
        logger.info("Event history cleared")


# Global event bus instance
_global_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get global event bus instance"""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


if __name__ == "__main__":
    # Test event bus
    import asyncio
    
    async def test():
        print("Testing Event Bus")
        print("=" * 50)
        
        bus = EventBus()
        
        # Define handlers
        def sync_handler(event: Event):
            print(f"Sync handler: {event.type} - {event.data}")
        
        async def async_handler(event: Event):
            print(f"Async handler: {event.type} - {event.data}")
            await asyncio.sleep(0.1)
        
        # Subscribe
        bus.subscribe(EventType.MODEL_LOADED, sync_handler)
        bus.subscribe(EventType.MODEL_LOADED, async_handler)
        
        # Publish
        await bus.publish(
            EventType.MODEL_LOADED,
            {"model": "phi-3-mini", "ram_mb": 2000},
            source="test"
        )
        
        # Wait for async handlers
        await asyncio.sleep(0.2)
        
        # Get stats
        stats = bus.get_stats()
        print(f"\nStats: {stats}")
        
        # Get history
        history = bus.get_history(last_n=5)
        print(f"History: {len(history)} events")
        
        print("=" * 50)
    
    asyncio.run(test())
