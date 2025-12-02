"""
Resource Monitor - Real-Time RAM Tracking and Alerts
Monitors system resources and provides alerts before crashes
"""

import psutil
import logging
import threading
import time
from typing import Callable, Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ResourceSnapshot:
    """Snapshot of system resources at a point in time"""
    timestamp: datetime
    ram_total_gb: float
    ram_available_gb: float
    ram_used_gb: float
    ram_percent: float
    cpu_percent: float
    
    @property
    def status(self) -> str:
        """Get status based on RAM usage"""
        if self.ram_percent > 90:
            return "critical"
        elif self.ram_percent > 75:
            return "warning"
        else:
            return "ok"


class ResourceMonitor:
    """
    Real-time resource monitoring with alerts
    """
    
    def __init__(
        self,
        check_interval: float = 1.0,
        warning_threshold: float = 75.0,
        critical_threshold: float = 90.0
    ):
        """
        Initialize resource monitor
        
        Args:
            check_interval: Seconds between checks
            warning_threshold: RAM % for warning
            critical_threshold: RAM % for critical alert
        """
        self.check_interval = check_interval
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable[[ResourceSnapshot], None]] = []
        self._history: List[ResourceSnapshot] = []
        self._max_history = 60  # Keep last 60 snapshots
        
        logger.info(
            f"ResourceMonitor initialized: "
            f"interval={check_interval}s, "
            f"warning={warning_threshold}%, "
            f"critical={critical_threshold}%"
        )
    
    def get_snapshot(self) -> ResourceSnapshot:
        """Get current resource snapshot"""
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.1)
        
        return ResourceSnapshot(
            timestamp=datetime.now(),
            ram_total_gb=mem.total / (1024 ** 3),
            ram_available_gb=mem.available / (1024 ** 3),
            ram_used_gb=mem.used / (1024 ** 3),
            ram_percent=mem.percent,
            cpu_percent=cpu
        )
    
    def add_callback(self, callback: Callable[[ResourceSnapshot], None]):
        """
        Add callback to be called on each check
        
        Args:
            callback: Function that receives ResourceSnapshot
        """
        self._callbacks.append(callback)
        logger.debug(f"Added callback: {callback.__name__}")
    
    def start(self):
        """Start monitoring in background thread"""
        if self._monitoring:
            logger.warning("Monitor already running")
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="ResourceMonitor"
        )
        self._monitor_thread.start()
        logger.info("Resource monitoring started")
    
    def stop(self):
        """Stop monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
        logger.info("Resource monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self._monitoring:
            try:
                snapshot = self.get_snapshot()
                
                # Add to history
                self._history.append(snapshot)
                if len(self._history) > self._max_history:
                    self._history.pop(0)
                
                # Check thresholds
                if snapshot.ram_percent > self.critical_threshold:
                    logger.critical(
                        f"CRITICAL: RAM usage at {snapshot.ram_percent:.1f}% "
                        f"({snapshot.ram_used_gb:.1f}GB / {snapshot.ram_total_gb:.1f}GB)"
                    )
                elif snapshot.ram_percent > self.warning_threshold:
                    logger.warning(
                        f"WARNING: RAM usage at {snapshot.ram_percent:.1f}% "
                        f"({snapshot.ram_used_gb:.1f}GB / {snapshot.ram_total_gb:.1f}GB)"
                    )
                
                # Call callbacks
                for callback in self._callbacks:
                    try:
                        callback(snapshot)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
                
                time.sleep(self.check_interval)
            
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                time.sleep(self.check_interval)
    
    def get_history(self, last_n: int = 10) -> List[ResourceSnapshot]:
        """
        Get recent history
        
        Args:
            last_n: Number of recent snapshots
        
        Returns:
            List of recent snapshots
        """
        return self._history[-last_n:]
    
    def get_stats(self) -> Dict[str, any]:
        """
        Get statistics from history
        
        Returns:
            Dictionary with min/max/avg stats
        """
        if not self._history:
            return {}
        
        ram_percents = [s.ram_percent for s in self._history]
        cpu_percents = [s.cpu_percent for s in self._history]
        
        return {
            "ram": {
                "current": self._history[-1].ram_percent,
                "min": min(ram_percents),
                "max": max(ram_percents),
                "avg": sum(ram_percents) / len(ram_percents)
            },
            "cpu": {
                "current": self._history[-1].cpu_percent,
                "min": min(cpu_percents),
                "max": max(cpu_percents),
                "avg": sum(cpu_percents) / len(cpu_percents)
            },
            "samples": len(self._history)
        }


# Global monitor instance
_global_monitor: Optional[ResourceMonitor] = None


def get_monitor() -> ResourceMonitor:
    """Get global resource monitor instance"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = ResourceMonitor()
    return _global_monitor


def start_monitoring():
    """Start global resource monitoring"""
    monitor = get_monitor()
    monitor.start()


def stop_monitoring():
    """Stop global resource monitoring"""
    monitor = get_monitor()
    monitor.stop()


if __name__ == "__main__":
    # Test resource monitor
    print("Testing Resource Monitor")
    print("=" * 50)
    
    def alert_callback(snapshot: ResourceSnapshot):
        if snapshot.status != "ok":
            print(
                f"[{snapshot.timestamp.strftime('%H:%M:%S')}] "
                f"ALERT: RAM {snapshot.ram_percent:.1f}% - {snapshot.status.upper()}"
            )
    
    monitor = ResourceMonitor(check_interval=2.0)
    monitor.add_callback(alert_callback)
    monitor.start()
    
    print("Monitoring for 10 seconds...")
    time.sleep(10)
    
    monitor.stop()
    
    stats = monitor.get_stats()
    print("\nStatistics:")
    print(f"RAM: {stats['ram']['avg']:.1f}% avg, "
          f"{stats['ram']['min']:.1f}% min, "
          f"{stats['ram']['max']:.1f}% max")
    print(f"CPU: {stats['cpu']['avg']:.1f}% avg")
    print("=" * 50)
