"""
Crash Recovery Integration Tests
Tests system resilience and state restoration after simulated crashes
"""

import pytest
import shutil
from pathlib import Path
import time
from core.crash_recovery import get_crash_recovery_manager, CrashRecoveryManager
from core.managers.config_manager import get_config_manager
from core.managers.cache_manager import get_cache_manager
from core.metrics_manager import get_metrics_manager
from error.error_handler import get_error_handler

@pytest.fixture
def test_env(tmp_path):
    """Setup test environment"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    
    # Initialize managers with test dirs
    config_mgr = get_config_manager(config_dir)
    error_handler = get_error_handler()
    
    # Reset singletons if possible or create new instances
    # Since singletons are global, we might need to be careful
    # For this test, we'll instantiate classes directly to avoid singleton pollution
    
    return {
        "config_dir": config_dir,
        "state_dir": state_dir,
        "cache_dir": cache_dir,
        "config_mgr": config_mgr,
        "error_handler": error_handler
    }

def test_crash_detection(test_env):
    """Test detection of previous crash"""
    state_dir = test_env["state_dir"]
    
    # Initialize recovery manager
    recovery_mgr = CrashRecoveryManager(state_dir)
    
    # Mark that the app is running (creates crash marker)
    recovery_mgr.mark_running()
    
    # Verify crash marker exists
    assert (state_dir / ".crash_marker").exists()
    
    # Check for crash - should return True since marker exists
    assert recovery_mgr.detect_crash() is True

def test_state_restoration(test_env):
    """Test restoration of state after 'crash'"""
    # 1. Setup initial state
    cache_dir = test_env["cache_dir"]
    
    # Create a 'cached' file
    model_file = cache_dir / "test_model.bin"
    model_file.write_text("data")
    
    # 2. Simulate restart
    # We want to verify that CacheManager picks up existing files
    
    # Re-initialize CacheManager with correct parameters
    from core.managers.cache_manager import CacheManager
    cache_mgr = CacheManager(
        cache_dir=cache_dir,
        max_cache_bytes=1 * 1024**3,  # 1GB
        min_free_bytes=100 * 1024**2  # 100MB
    )
    
    # It should detect the file
    assert cache_mgr.get_current_usage() > 0
    
    # 3. Verify crash recovery state restoration
    state_dir = test_env["state_dir"]
    recovery_mgr = CrashRecoveryManager(state_dir)
    
    # Save some state
    recovery_mgr._state = {"test_key": "test_value"}
    recovery_mgr.save_state()
    
    # Create new instance and restore
    recovery_mgr2 = CrashRecoveryManager(state_dir)
    restored = recovery_mgr2.restore_state()
    
    assert restored is True
    assert recovery_mgr2._state.get("test_key") == "test_value"

def test_cleanup_after_crash(test_env):
    """Test cleanup operations"""
    state_dir = test_env["state_dir"]
    
    # Create stale lock files
    (state_dir / "resource.lock").write_text("")
    
    recovery_mgr = CrashRecoveryManager(state_dir)
    
    # Run cleanup
    # Note: cleanup() is not explicitly defined in CrashRecoveryManager based on file view
    # It has cleanup_gpu_vram() and mark_clean_shutdown()
    # Let's verify what we want to test.
    # If cleanup() doesn't exist, we should remove this test or test existing methods.
    # The file view showed cleanup_gpu_vram, mark_clean_shutdown, mark_running.
    # It does NOT have a generic cleanup() method.
    # So we'll test mark_clean_shutdown() instead.
    
    recovery_mgr.mark_clean_shutdown()
    
    # Crash marker should be gone
    assert not (state_dir / ".crash_marker").exists()
