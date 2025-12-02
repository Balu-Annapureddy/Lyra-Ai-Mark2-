"""
Global Thread-Safe State Manager
Manages application state, user settings, model state, and runtime flags
"""

import logging
import threading
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

from core.paths import get_config_dir
from core.errors import StateError, StateCorruptedError, StateLockError

logger = logging.getLogger(__name__)


@dataclass
class UserSettings:
    """User settings"""
    theme: str = "dark"
    language: str = "en"
    voice_enabled: bool = True
    notifications_enabled: bool = True
    auto_save: bool = True
    performance_mode: str = "auto"  # "auto", "low_power", "high_performance"


@dataclass
class ModelState:
    """Model state"""
    llm_loaded: bool = False
    llm_model: Optional[str] = None
    stt_loaded: bool = False
    stt_model: Optional[str] = None
    tts_loaded: bool = False
    tts_engine: Optional[str] = None
    vision_loaded: bool = False


@dataclass
class RuntimeFlags:
    """Runtime flags"""
    safe_startup: bool = True
    warmup_enabled: bool = True
    monitoring_enabled: bool = True
    debug_mode: bool = False
    offline_mode: bool = False


class StateManager:
    """
    Thread-safe global state manager
    Manages user settings, model state, and runtime flags
    """
    
    def __init__(self):
        """Initialize state manager"""
        self._lock = threading.RLock()
        self._state_file = get_config_dir() / "state.json"
        
        # State components
        self.user_settings = UserSettings()
        self.model_state = ModelState()
        self.runtime_flags = RuntimeFlags()
        
        # Runtime data
        self._session_id: Optional[str] = None
        self._session_start: Optional[datetime] = None
        self._custom_data: Dict[str, Any] = {}
        
        # Load persisted state
        self._load_state()
        
        logger.info("StateManager initialized")
    
    def _load_state(self):
        """Load state from disk"""
        if not self._state_file.exists():
            logger.info("No saved state found, using defaults")
            return
        
        # Check for corruption
        if self._is_state_corrupted():
            logger.error("State file corrupted, attempting restore from backup")
            if self._restore_from_backup():
                return
            else:
                logger.warning("Backup restore failed, using defaults")
                return
        
        try:
            with open(self._state_file, 'r') as f:
                data = json.load(f)
            
            # Load user settings
            if "user_settings" in data:
                self.user_settings = UserSettings(**data["user_settings"])
            
            # Load runtime flags (but not model state - that's session-specific)
            if "runtime_flags" in data:
                self.runtime_flags = RuntimeFlags(**data["runtime_flags"])
            
            # Load custom data
            if "custom_data" in data:
                self._custom_data = data["custom_data"]
            
            logger.info("State loaded from disk")
        
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            # Try backup
            if self._restore_from_backup():
                logger.info("Recovered from backup")
            else:
                raise StateCorruptedError(f"State file corrupted and backup failed: {e}")
    
    def _save_state(self):
        """Save state to disk"""
        try:
            data = {
                "user_settings": asdict(self.user_settings),
                "runtime_flags": asdict(self.runtime_flags),
                "custom_data": self._custom_data,
                "last_saved": datetime.now().isoformat()
            }
            
            # Create backup before saving
            if self._state_file.exists():
                backup_file = self._state_file.with_suffix('.json.bak')
                self._state_file.replace(backup_file)
            
            # Atomic write
            temp_file = self._state_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            temp_file.replace(self._state_file)
            logger.debug("State saved to disk")
        
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def _restore_from_backup(self) -> bool:
        """
        Restore state from backup file
        
        Returns:
            True if restored successfully
        """
        backup_file = self._state_file.with_suffix('.json.bak')
        
        if not backup_file.exists():
            logger.warning("No backup file found")
            return False
        
        try:
            with open(backup_file, 'r') as f:
                data = json.load(f)
            
            # Restore user settings
            if "user_settings" in data:
                self.user_settings = UserSettings(**data["user_settings"])
            
            # Restore runtime flags
            if "runtime_flags" in data:
                self.runtime_flags = RuntimeFlags(**data["runtime_flags"])
            
            # Restore custom data
            if "custom_data" in data:
                self._custom_data = data["custom_data"]
            
            logger.info("State restored from backup")
            return True
        
        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            return False
    
    def _is_state_corrupted(self) -> bool:
        """
        Check if state file is corrupted
        
        Returns:
            True if corrupted
        """
        if not self._state_file.exists():
            return False
        
        try:
            with open(self._state_file, 'r') as f:
                json.load(f)
            return False
        except:
            return True
    
    # User Settings Methods
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get user setting
        
        Args:
            key: Setting key
            default: Default value if not found
        
        Returns:
            Setting value
        """
        with self._lock:
            return getattr(self.user_settings, key, default)
    
    def set_setting(self, key: str, value: Any, persist: bool = True):
        """
        Set user setting
        
        Args:
            key: Setting key
            value: Setting value
            persist: Save to disk
        """
        with self._lock:
            if not hasattr(self.user_settings, key):
                raise StateError(f"Unknown setting: {key}")
            
            setattr(self.user_settings, key, value)
            logger.info(f"Setting updated: {key} = {value}")
            
            if persist:
                self._save_state()
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all user settings"""
        with self._lock:
            return asdict(self.user_settings)
    
    # Model State Methods
    def set_model_loaded(
        self,
        model_type: str,
        model_name: str,
        loaded: bool = True
    ):
        """
        Set model loaded state
        
        Args:
            model_type: "llm", "stt", "tts", or "vision"
            model_name: Model identifier
            loaded: Whether model is loaded
        """
        with self._lock:
            if model_type == "llm":
                self.model_state.llm_loaded = loaded
                self.model_state.llm_model = model_name if loaded else None
            elif model_type == "stt":
                self.model_state.stt_loaded = loaded
                self.model_state.stt_model = model_name if loaded else None
            elif model_type == "tts":
                self.model_state.tts_loaded = loaded
                self.model_state.tts_engine = model_name if loaded else None
            elif model_type == "vision":
                self.model_state.vision_loaded = loaded
            else:
                raise StateError(f"Unknown model type: {model_type}")
            
            logger.info(f"Model state updated: {model_type} = {model_name} (loaded={loaded})")
    
    def is_model_loaded(self, model_type: str) -> bool:
        """Check if model is loaded"""
        with self._lock:
            if model_type == "llm":
                return self.model_state.llm_loaded
            elif model_type == "stt":
                return self.model_state.stt_loaded
            elif model_type == "tts":
                return self.model_state.tts_loaded
            elif model_type == "vision":
                return self.model_state.vision_loaded
            return False
    
    def get_model_state(self) -> Dict[str, Any]:
        """Get all model states"""
        with self._lock:
            return asdict(self.model_state)
    
    # Runtime Flags Methods
    def get_flag(self, key: str, default: bool = False) -> bool:
        """Get runtime flag"""
        with self._lock:
            return getattr(self.runtime_flags, key, default)
    
    def set_flag(self, key: str, value: bool, persist: bool = False):
        """
        Set runtime flag
        
        Args:
            key: Flag key
            value: Flag value
            persist: Save to disk
        """
        with self._lock:
            if not hasattr(self.runtime_flags, key):
                raise StateError(f"Unknown flag: {key}")
            
            setattr(self.runtime_flags, key, value)
            logger.info(f"Flag updated: {key} = {value}")
            
            if persist:
                self._save_state()
    
    def get_all_flags(self) -> Dict[str, bool]:
        """Get all runtime flags"""
        with self._lock:
            return asdict(self.runtime_flags)
    
    # Custom Data Methods
    def set_data(self, key: str, value: Any, persist: bool = True):
        """
        Set custom data
        
        Args:
            key: Data key
            value: Data value (must be JSON-serializable)
            persist: Save to disk
        """
        with self._lock:
            self._custom_data[key] = value
            
            if persist:
                self._save_state()
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get custom data"""
        with self._lock:
            return self._custom_data.get(key, default)
    
    def delete_data(self, key: str, persist: bool = True):
        """Delete custom data"""
        with self._lock:
            if key in self._custom_data:
                del self._custom_data[key]
                
                if persist:
                    self._save_state()
    
    # Session Methods
    def start_session(self, session_id: Optional[str] = None):
        """
        Start new session
        
        Args:
            session_id: Optional session identifier
        """
        with self._lock:
            self._session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
            self._session_start = datetime.now()
            logger.info(f"Session started: {self._session_id}")
    
    def get_session_id(self) -> Optional[str]:
        """Get current session ID"""
        with self._lock:
            return self._session_id
    
    def get_session_duration(self) -> Optional[float]:
        """Get session duration in seconds"""
        with self._lock:
            if self._session_start:
                return (datetime.now() - self._session_start).total_seconds()
            return None
    
    # Utility Methods
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        with self._lock:
            self.user_settings = UserSettings()
            self.runtime_flags = RuntimeFlags()
            self._custom_data = {}
            self._save_state()
            logger.info("State reset to defaults")
    
    def get_full_state(self) -> Dict[str, Any]:
        """Get complete state snapshot"""
        with self._lock:
            return {
                "user_settings": asdict(self.user_settings),
                "model_state": asdict(self.model_state),
                "runtime_flags": asdict(self.runtime_flags),
                "custom_data": self._custom_data,
                "session_id": self._session_id,
                "session_duration": self.get_session_duration()
            }


# Global state manager instance
_global_state: Optional[StateManager] = None
_state_lock = threading.Lock()


def get_state_manager() -> StateManager:
    """Get global state manager instance (thread-safe)"""
    global _global_state
    
    if _global_state is None:
        with _state_lock:
            if _global_state is None:
                _global_state = StateManager()
    
    return _global_state


if __name__ == "__main__":
    # Test state manager
    print("Testing State Manager")
    print("=" * 50)
    
    state = StateManager()
    
    # Test settings
    state.set_setting("theme", "light")
    print(f"Theme: {state.get_setting('theme')}")
    
    # Test model state
    state.set_model_loaded("llm", "phi-3-mini", True)
    print(f"LLM loaded: {state.is_model_loaded('llm')}")
    
    # Test flags
    state.set_flag("debug_mode", True)
    print(f"Debug mode: {state.get_flag('debug_mode')}")
    
    # Test custom data
    state.set_data("test_key", {"value": 123})
    print(f"Custom data: {state.get_data('test_key')}")
    
    # Test session
    state.start_session()
    print(f"Session ID: {state.get_session_id()}")
    
    print("\nFull state:")
    import json
    print(json.dumps(state.get_full_state(), indent=2, default=str))
    
    print("=" * 50)
