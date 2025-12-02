"""
Memory Watchdog - RAM Monitoring and Protection
Monitors system RAM with soft/hard limits and auto-recovery
"""

import logging
import psutil
import threading
import time
from typing import Optional, Callable, Dict, Any
from datetime import datetime
import gc

from core.events import get_event_bus, EventType

logger = logging.getLogger(__name__)


class MemoryWatchdog:
    """
    Monitors system RAM and triggers actions on limits
    - Soft limit: Warning + garbage collection
    - Hard limit: Emergency unload + module restart
    """
    
    def __init__(
        self,
        soft_limit_percent: float = 75.0,
        hard_limit_percent: float = 90.0,
        check_interval: int = 10,
        enabled: bool = True
    ):
        """
        Initialize memory watchdog
        
        Args:
            soft_limit_percent: Soft limit (warning + GC)
            hard_limit_percent: Hard limit (emergency actions)
            check_interval: Check interval in seconds
            enabled: Whether watchdog is enabled
        """
        self.soft_limit = soft_limit_percent
        self.hard_limit = hard_limit_percent
        self.check_interval = check_interval
        self.enabled = enabled
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._peak_usage = 0.0
        self._soft_limit_triggered = False
        self._hard_limit_triggered = False
        
        # Callbacks
        self._soft_limit_callback: Optional[Callable] = None
        self._hard_limit_callback: Optional[Callable] = None
        
        # Event bus
        self.event_bus = get_event_bus()
        
        logger.info(
            f"MemoryWatchdog initialized: "
            f"soft={soft_limit_percent}%, hard={hard_limit_percent}%, "
            f"enabled={enabled}"
        )
    
    @classmethod
    def from_config(cls, config_manager) -> "MemoryWatchdog":
        """
        Create MemoryWatchdog from configuration file
        
        Args:
            config_manager: ConfigManager instance
            
        Returns:
            MemoryWatchdog instance
        """
        from pathlib import Path
        
        try:
            config = config_manager.load_yaml("memory_watchdog.yaml", required=False)
            
            if config is None:
                logger.warning("No memory watchdog config found, using defaults")
                return cls()
            
            # Get base settings
            enabled = config.get("enabled", False)
            soft_limit = config.get("soft_limit_percent", 75.0)
            hard_limit = config.get("hard_limit_percent", 90.0)
            check_interval = config.get("check_interval", 10)
            
            # Auto-adjustment for low-RAM systems
            auto_adjust = config.get("auto_adjust", True)
            
            if auto_adjust:
                import psutil
                total_ram_gb = psutil.virtual_memory().total / (1024 ** 3)
                low_ram_threshold = config.get("low_ram_threshold_gb", 8.0)
                
                if total_ram_gb < low_ram_threshold:
                    logger.info(
                        f"Low RAM system detected ({total_ram_gb:.2f} GB), "
                        f"adjusting watchdog limits"
                    )
                    soft_limit = config.get("low_ram_soft_limit", 85.0)
                    hard_limit = config.get("low_ram_hard_limit", 95.0)
            
            return cls(
                soft_limit_percent=soft_limit,
                hard_limit_percent=hard_limit,
                check_interval=check_interval,
                enabled=enabled
            )
        
        except Exception as e:
            logger.error(f"Failed to load watchdog config: {e}, using defaults")
            return cls()
    
    def set_soft_limit_callback(self, callback: Callable):
        """Set callback for soft limit"""
        self._soft_limit_callback = callback
    
    def set_hard_limit_callback(self, callback: Callable):
        """Set callback for hard limit"""
        self._hard_limit_callback = callback
    
    def start(self):
        """Start monitoring"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="MemoryWatchdog"
        )
        self._thread.start()
        logger.info("Memory watchdog started")
    
    def stop(self):
        """Stop monitoring"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("Memory watchdog stopped")
    
    def _monitor_loop(self):
        """Monitoring loop"""
        while self._running:
            try:
                # Get memory usage
                mem = psutil.virtual_memory()
                percent = mem.percent
                
                # Update peak
                if percent > self._peak_usage:
                    self._peak_usage = percent
                
                # Check soft limit
                if percent >= self.soft_limit and not self._soft_limit_triggered:
                    self._handle_soft_limit(percent, mem)
                    self._soft_limit_triggered = True
                elif percent < self.soft_limit:
                    self._soft_limit_triggered = False
                
                # Check hard limit
                if percent >= self.hard_limit and not self._hard_limit_triggered:
                    self._handle_hard_limit(percent, mem)
                    self._hard_limit_triggered = True
                elif percent < self.hard_limit:
                    self._hard_limit_triggered = False
                
                time.sleep(self.check_interval)
            
            except Exception as e:
                logger.error(f"Memory watchdog error: {e}")
                time.sleep(self.check_interval)
    
    def _handle_soft_limit(self, percent: float, mem: Any):
        """Handle soft limit breach"""
        logger.warning(
            f"Soft memory limit reached: {percent:.1f}% "
            f"({mem.used // (1024**3)}GB / {mem.total // (1024**3)}GB)"
        )
        
        # Publish event
        self.event_bus.publish_sync(
            EventType.MEMORY_WARNING,
            {
                "percent": percent,
                "used_gb": mem.used / (1024**3),
                "total_gb": mem.total / (1024**3),
                "available_gb": mem.available / (1024**3)
            },
            source="memory_watchdog"
        )
        
        # Force garbage collection
        logger.info("Running garbage collection...")
        gc.collect()
        
        # Call callback
        if self._soft_limit_callback:
            try:
                self._soft_limit_callback(percent, mem)
            except Exception as e:
                logger.error(f"Soft limit callback error: {e}")
    
    def _handle_hard_limit(self, percent: float, mem: Any):
        """Handle hard limit breach"""
        logger.error(
            f"HARD memory limit reached: {percent:.1f}% "
            f"({mem.used // (1024**3)}GB / {mem.total // (1024**3)}GB)"
        )
        
        # Publish event
        self.event_bus.publish_sync(
            EventType.MEMORY_CRITICAL,
            {
                "percent": percent,
                "used_gb": mem.used / (1024**3),
                "total_gb": mem.total / (1024**3),
                "available_gb": mem.available / (1024**3),
                "action": "emergency_unload"
            },
            source="memory_watchdog"
        )
        
        # Emergency actions
        logger.warning("Triggering emergency memory recovery...")
        
        # 1. Aggressive garbage collection
        gc.collect()
        gc.collect()  # Run twice
        
        # 2. Unload models (via callback)
        if self._hard_limit_callback:
            try:
                self._hard_limit_callback(percent, mem)
            except Exception as e:
                logger.error(f"Hard limit callback error: {e}")
    
    def get_current_usage(self) -> Dict[str, Any]:
        """Get current memory usage"""
        mem = psutil.virtual_memory()
        
        return {
            "percent": mem.percent,
            "used_gb": mem.used / (1024**3),
            "available_gb": mem.available / (1024**3),
            "total_gb": mem.total / (1024**3),
            "peak_percent": self._peak_usage
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get watchdog statistics"""
        usage = self.get_current_usage()
        
        return {
            **usage,
            "soft_limit": self.soft_limit,
            "hard_limit": self.hard_limit,
            "soft_limit_active": self._soft_limit_triggered,
            "hard_limit_active": self._hard_limit_triggered,
            "running": self._running
        }
    
    def reset_peak(self):
        """Reset peak usage counter"""
        self._peak_usage = 0.0
        logger.info("Peak memory usage reset")


# Global watchdog instance
_global_watchdog: Optional[MemoryWatchdog] = None


def get_memory_watchdog() -> MemoryWatchdog:
    """Get global memory watchdog instance"""
    global _global_watchdog
    if _global_watchdog is None:
        _global_watchdog = MemoryWatchdog()
    return _global_watchdog


if __name__ == "__main__":
    # Test memory watchdog
    print("Testing Memory Watchdog")
    print("=" * 50)
    
    def soft_limit_handler(percent, mem):
        print(f"Soft limit triggered: {percent:.1f}%")
    
    def hard_limit_handler(percent, mem):
        print(f"HARD limit triggered: {percent:.1f}%")
    
    watchdog = MemoryWatchdog(
        soft_limit_percent=50.0,  # Low for testing
        hard_limit_percent=60.0,
        check_interval=2
    )
    
    watchdog.set_soft_limit_callback(soft_limit_handler)
    watchdog.set_hard_limit_callback(hard_limit_handler)
    
    watchdog.start()
    
    # Get stats
    stats = watchdog.get_stats()
    print(f"Current usage: {stats['percent']:.1f}%")
    print(f"Peak usage: {stats['peak_percent']:.1f}%")
    
    # Run for a bit
    time.sleep(5)
    
    watchdog.stop()
    print("=" * 50)
