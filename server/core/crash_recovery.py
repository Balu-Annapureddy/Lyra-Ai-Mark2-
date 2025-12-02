"""
Crash Recovery Manager
Handles crash detection, graceful model unloading, and state persistence
"""

import json
import schedule
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from core.structured_logger import get_structured_logger


class CrashRecoveryManager:
    """
    Manages crash recovery with graceful task draining and scheduled state persistence
    
    Features:
    - Graceful task draining before model unload
    - Scheduled state persistence (not continuous)
    - Crash detection and recovery
    - GPU VRAM cleanup
    """
    
    def __init__(self, state_dir: Path, save_interval: int = 60):
        """
        Initialize crash recovery manager
        
        Args:
            state_dir: Directory for state files
            save_interval: State save interval in seconds
        """
        self.struct_logger = get_structured_logger("CrashRecoveryManager")
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.save_interval = save_interval
        
        self.major_events = ['model_load', 'mode_switch', 'config_change']
        self._state: Dict[str, Any] = {}
        self._model_tasks: Dict[str, List[str]] = {}  # model_id -> task_ids
        
        self.struct_logger.info(
            "initialized",
            "Crash recovery manager initialized",
            state_dir=str(state_dir),
            save_interval=save_interval
        )
    
    def start_scheduled_saves(self):
        """Start scheduled state persistence"""
        schedule.every(self.save_interval).seconds.do(self.save_state)
        
        self.struct_logger.info(
            "scheduled_saves_started",
            f"Scheduled state saves every {self.save_interval}s"
        )
    
    def save_state(self):
        """Save current state to disk"""
        try:
            state_file = self.state_dir / "recovery_state.json"
            
            state_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "state": self._state,
                "model_tasks": self._model_tasks
            }
            
            with open(state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
            
            self.struct_logger.debug(
                "state_saved",
                "State saved successfully",
                state_file=str(state_file)
            )
            
        except Exception as e:
            self.struct_logger.error(
                "state_save_failed",
                f"Failed to save state: {e}",
                error=str(e)
            )
    
    def restore_state(self) -> bool:
        """
        Restore state from disk
        
        Returns:
            True if restored successfully
        """
        try:
            state_file = self.state_dir / "recovery_state.json"
            
            if not state_file.exists():
                self.struct_logger.info(
                    "no_state_file",
                    "No state file found, starting fresh"
                )
                return False
            
            with open(state_file, 'r') as f:
                state_data = json.load(f)
            
            self._state = state_data.get("state", {})
            self._model_tasks = state_data.get("model_tasks", {})
            
            self.struct_logger.info(
                "state_restored",
                "State restored successfully",
                timestamp=state_data.get("timestamp")
            )
            
            return True
            
        except Exception as e:
            self.struct_logger.error(
                "state_restore_failed",
                f"Failed to restore state: {e}",
                error=str(e)
            )
            return False
    
    def on_major_event(self, event_type: str):
        """
        Save state immediately on major events
        
        Args:
            event_type: Type of event
        """
        if event_type in self.major_events:
            self.struct_logger.info(
                "major_event_save",
                f"Saving state due to major event: {event_type}",
                event_type=event_type
            )
            self.save_state()
    
    def pause_model_tasks(self, model_id: str):
        """
        Pause accepting new tasks for a model
        
        Args:
            model_id: Model identifier
        """
        self.struct_logger.info(
            "model_tasks_paused",
            f"Paused new tasks for model: {model_id}",
            model_id=model_id
        )
        # Implementation would integrate with task queue
    
    def drain_tasks(self, model_id: str, timeout: int = 30) -> bool:
        """
        Wait for running tasks to complete
        
        Args:
            model_id: Model identifier
            timeout: Maximum wait time in seconds
            
        Returns:
            True if all tasks completed
        """
        import time
        start_time = time.time()
        
        self.struct_logger.info(
            "draining_tasks",
            f"Draining tasks for model {model_id}",
            model_id=model_id,
            timeout=timeout
        )
        
        # Wait for tasks to complete (simplified)
        while time.time() - start_time < timeout:
            running_tasks = self._model_tasks.get(model_id, [])
            if not running_tasks:
                self.struct_logger.info(
                    "drain_complete",
                    f"All tasks drained for model {model_id}",
                    model_id=model_id
                )
                return True
            time.sleep(1)
        
        self.struct_logger.warning(
            "drain_timeout",
            f"Task drain timed out for model {model_id}",
            model_id=model_id,
            remaining_tasks=len(self._model_tasks.get(model_id, []))
        )
        return False
    
    def unload_model_gracefully(self, model_id: str) -> bool:
        """
        Gracefully unload a model with task draining
        
        Args:
            model_id: Model identifier
            
        Returns:
            True if unloaded successfully
        """
        try:
            # Step 1: Stop accepting new tasks
            self.pause_model_tasks(model_id)
            
            # Step 2: Wait for running tasks to complete
            drained = self.drain_tasks(model_id, timeout=30)
            
            if not drained:
                self.struct_logger.warning(
                    "forced_unload",
                    f"Forcing model unload after drain timeout: {model_id}",
                    model_id=model_id
                )
            
            # Step 3: Unload model
            self.struct_logger.info(
                "model_unloading",
                f"Unloading model: {model_id}",
                model_id=model_id
            )
            # Actual unload would happen here
            
            # Step 4: Activate fallback if needed
            self.activate_fallback(model_id)
            
            return True
            
        except Exception as e:
            self.struct_logger.error(
                "unload_failed",
                f"Failed to unload model {model_id}: {e}",
                model_id=model_id,
                error=str(e)
            )
            return False
    
    def activate_fallback(self, model_id: str):
        """
        Activate fallback model
        
        Args:
            model_id: Original model identifier
        """
        self.struct_logger.info(
            "fallback_activated",
            f"Activating fallback for model: {model_id}",
            model_id=model_id
        )
        # Implementation would load fallback model
    
    def cleanup_gpu_vram(self):
        """Clean up GPU VRAM"""
        try:
            self.struct_logger.info("vram_cleanup", "Cleaning up GPU VRAM")
            
            # Try to import torch for GPU cleanup
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    self.struct_logger.info(
                        "vram_cleaned",
                        "GPU VRAM cache cleared"
                    )
            except ImportError:
                self.struct_logger.debug(
                    "no_torch",
                    "PyTorch not available, skipping GPU cleanup"
                )
                
        except Exception as e:
            self.struct_logger.error(
                "vram_cleanup_failed",
                f"Failed to cleanup VRAM: {e}",
                error=str(e)
            )
    
    def detect_crash(self) -> bool:
        """
        Detect if previous run crashed
        
        Returns:
            True if crash detected
        """
        crash_marker = self.state_dir / ".crash_marker"
        return crash_marker.exists()
    
    def mark_clean_shutdown(self):
        """Mark that shutdown was clean"""
        crash_marker = self.state_dir / ".crash_marker"
        if crash_marker.exists():
            crash_marker.unlink()
    
    def mark_running(self):
        """Mark that application is running"""
        crash_marker = self.state_dir / ".crash_marker"
        crash_marker.touch()
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for crash recovery manager"""
        return {
            "status": "ok",
            "component": "CrashRecoveryManager",
            "details": {
                "state_dir": str(self.state_dir),
                "save_interval": self.save_interval,
                "crash_detected": self.detect_crash()
            },
            "errors": [],
            "last_check": datetime.utcnow().isoformat()
        }


# Singleton instance
_crash_recovery: Optional[CrashRecoveryManager] = None


def get_crash_recovery_manager(state_dir: Optional[Path] = None) -> CrashRecoveryManager:
    """Get or create the global crash recovery manager"""
    global _crash_recovery
    if _crash_recovery is None:
        if state_dir is None:
            state_dir = Path("ai-worker/state")
        _crash_recovery = CrashRecoveryManager(state_dir)
    return _crash_recovery
