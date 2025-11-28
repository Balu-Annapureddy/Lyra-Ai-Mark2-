"""
Worker Watchdog
Monitors worker threads with cooperative timeout strategy (no thread killing)
"""

import threading
import time
from typing import Dict, Optional, Callable, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from core.structured_logger import get_structured_logger


class WorkerStatus(Enum):
    """Worker status enumeration"""
    IDLE = "idle"
    ACTIVE = "active"
    ZOMBIE = "zombie"
    TERMINATED = "terminated"


@dataclass
class WorkerInfo:
    """Information about a worker"""
    worker_id: str
    status: WorkerStatus
    current_task: Optional[str]
    started_at: Optional[datetime]
    last_heartbeat: datetime
    timeout_seconds: int


class WorkerWatchdog:
    """
    Monitors worker threads with cooperative timeout strategy
    
    Features:
    - No forced thread termination (safer)
    - Zombie marking for timed-out workers
    - Automatic worker respawning
    - Graceful cleanup after task completion
    """
    
    def __init__(
        self,
        default_timeout: int = 30,
        heartbeat_interval: int = 5,
        max_workers: int = 4,
        zombie_cleanup_delay: int = 300
    ):
        """
        Initialize worker watchdog
        
        Args:
            default_timeout: Default timeout in seconds
            heartbeat_interval: Heartbeat check interval
            max_workers: Maximum number of workers
            zombie_cleanup_delay: Delay before cleaning up zombies (seconds)
        """
        self.struct_logger = get_structured_logger("WorkerWatchdog")
        self.default_timeout = default_timeout
        self.heartbeat_interval = heartbeat_interval
        self.max_workers = max_workers
        self.zombie_cleanup_delay = zombie_cleanup_delay
        
        self._workers: Dict[str, WorkerInfo] = {}
        self._task_timeouts: Dict[str, int] = {
            "llm_inference": 60,
            "stt_processing": 30,
            "tts_generation": 20,
            "vision_processing": 45
        }
        
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        
        self.struct_logger.info(
            "initialized",
            "Worker watchdog initialized",
            max_workers=max_workers,
            default_timeout=default_timeout
        )
    
    def register_worker(self, worker_id: str) -> bool:
        """
        Register a new worker
        
        Args:
            worker_id: Worker identifier
            
        Returns:
            True if registered successfully
        """
        if len(self._workers) >= self.max_workers:
            self.struct_logger.warning(
                "max_workers_reached",
                f"Cannot register worker: max workers ({self.max_workers}) reached",
                worker_id=worker_id
            )
            return False
        
        self._workers[worker_id] = WorkerInfo(
            worker_id=worker_id,
            status=WorkerStatus.IDLE,
            current_task=None,
            started_at=None,
            last_heartbeat=datetime.utcnow(),
            timeout_seconds=self.default_timeout
        )
        
        self.struct_logger.info(
            "worker_registered",
            f"Worker registered: {worker_id}",
            worker_id=worker_id
        )
        
        return True
    
    def start_task(self, worker_id: str, task_type: str, task_id: str):
        """
        Mark worker as starting a task
        
        Args:
            worker_id: Worker identifier
            task_type: Type of task
            task_id: Task identifier
        """
        if worker_id not in self._workers:
            self.struct_logger.error(
                "unknown_worker",
                f"Unknown worker: {worker_id}",
                worker_id=worker_id
            )
            return
        
        worker = self._workers[worker_id]
        worker.status = WorkerStatus.ACTIVE
        worker.current_task = task_id
        worker.started_at = datetime.utcnow()
        worker.timeout_seconds = self._task_timeouts.get(task_type, self.default_timeout)
        worker.last_heartbeat = datetime.utcnow()
        
        self.struct_logger.info(
            "task_started",
            f"Worker {worker_id} started task {task_id}",
            worker_id=worker_id,
            task_id=task_id,
            task_type=task_type,
            timeout=worker.timeout_seconds
        )
    
    def heartbeat(self, worker_id: str):
        """
        Record worker heartbeat
        
        Args:
            worker_id: Worker identifier
        """
        if worker_id in self._workers:
            self._workers[worker_id].last_heartbeat = datetime.utcnow()
    
    def complete_task(self, worker_id: str):
        """
        Mark task as complete
        
        Args:
            worker_id: Worker identifier
        """
        if worker_id not in self._workers:
            return
        
        worker = self._workers[worker_id]
        
        # If zombie, mark for cleanup
        if worker.status == WorkerStatus.ZOMBIE:
            self.struct_logger.info(
                "zombie_completed",
                f"Zombie worker {worker_id} completed task, scheduling cleanup",
                worker_id=worker_id
            )
            worker.status = WorkerStatus.TERMINATED
            # Schedule cleanup
            threading.Timer(
                self.zombie_cleanup_delay,
                self._cleanup_worker,
                args=[worker_id]
            ).start()
        else:
            worker.status = WorkerStatus.IDLE
            worker.current_task = None
            worker.started_at = None
        
        self.struct_logger.info(
            "task_completed",
            f"Worker {worker_id} completed task",
            worker_id=worker_id
        )
    
    def start(self):
        """Start monitoring workers"""
        if self._running:
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="WorkerWatchdog"
        )
        self._monitor_thread.start()
        
        self.struct_logger.info("watchdog_started", "Worker watchdog started")
    
    def stop(self):
        """Stop monitoring"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
        
        self.struct_logger.info("watchdog_stopped", "Worker watchdog stopped")
    
    def _monitor_loop(self):
        """Monitor loop - checks for timeouts"""
        while self._running:
            try:
                self._check_timeouts()
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                self.struct_logger.error(
                    "monitor_error",
                    f"Error in monitor loop: {e}",
                    error=str(e)
                )
    
    def _check_timeouts(self):
        """Check for worker timeouts"""
        now = datetime.utcnow()
        
        for worker_id, worker in list(self._workers.items()):
            if worker.status != WorkerStatus.ACTIVE:
                continue
            
            if worker.started_at is None:
                continue
            
            # Check if timed out
            elapsed = (now - worker.last_heartbeat).total_seconds()
            
            if elapsed > worker.timeout_seconds:
                self._handle_timeout(worker_id, worker, elapsed)
    
    def _handle_timeout(self, worker_id: str, worker: WorkerInfo, elapsed: float):
        """
        Handle worker timeout using cooperative strategy
        
        Args:
            worker_id: Worker identifier
            worker: Worker info
            elapsed: Elapsed time since last heartbeat
        """
        self.struct_logger.warning(
            "worker_timeout",
            f"Worker {worker_id} timed out after {elapsed:.1f}s",
            worker_id=worker_id,
            task_id=worker.current_task,
            elapsed_seconds=elapsed,
            timeout_seconds=worker.timeout_seconds
        )
        
        # Mark as zombie (don't kill)
        worker.status = WorkerStatus.ZOMBIE
        
        # Spawn replacement worker
        new_worker_id = f"{worker_id}_replacement_{int(time.time())}"
        self.register_worker(new_worker_id)
        
        self.struct_logger.info(
            "worker_replaced",
            f"Spawned replacement worker for {worker_id}",
            zombie_worker=worker_id,
            new_worker=new_worker_id
        )
    
    def _cleanup_worker(self, worker_id: str):
        """Clean up terminated worker"""
        if worker_id in self._workers:
            del self._workers[worker_id]
            self.struct_logger.info(
                "worker_cleaned_up",
                f"Cleaned up worker: {worker_id}",
                worker_id=worker_id
            )
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """Get worker statistics"""
        stats = {
            "total": len(self._workers),
            "active": sum(1 for w in self._workers.values() if w.status == WorkerStatus.ACTIVE),
            "idle": sum(1 for w in self._workers.values() if w.status == WorkerStatus.IDLE),
            "zombies": sum(1 for w in self._workers.values() if w.status == WorkerStatus.ZOMBIE),
            "terminated": sum(1 for w in self._workers.values() if w.status == WorkerStatus.TERMINATED)
        }
        return stats
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for worker watchdog"""
        stats = self.get_worker_stats()
        
        # Determine status
        if stats["zombies"] > 2:
            status = "degraded"
        elif stats["zombies"] > 5:
            status = "error"
        else:
            status = "ok"
        
        return {
            "status": status,
            "component": "WorkerWatchdog",
            "details": {
                "running": self._running,
                "worker_stats": stats,
                "max_workers": self.max_workers
            },
            "errors": [],
            "last_check": datetime.utcnow().isoformat()
        }


# Singleton instance
_worker_watchdog: Optional[WorkerWatchdog] = None


def get_worker_watchdog() -> WorkerWatchdog:
    """Get or create the global worker watchdog"""
    global _worker_watchdog
    if _worker_watchdog is None:
        _worker_watchdog = WorkerWatchdog()
    return _worker_watchdog
