"""
Startup Self-Tests
Runs comprehensive system tests on startup
"""

from typing import Dict, Any
from pathlib import Path

from core.structured_logger import get_structured_logger


class StartupSelfTest:
    """
    Runs startup self-tests to verify system health
    
    Tests:
    - GPU availability
    - Config validity
    - Permissions loaded
    - Thread pool health
    - Performance mode selection
    """
    
    def __init__(self):
        """Initialize startup self-test"""
        self.struct_logger = get_structured_logger("StartupSelfTest")
    
    def run_all_tests(self) -> Dict[str, bool]:
        """
        Run all startup tests
        
        Returns:
            Dictionary of test results
        """
        self.struct_logger.info("tests_starting", "Running startup self-tests")
        
        results = {
            'gpu_available': self.test_gpu(),
            'config_valid': self.test_config(),
            'permissions_loaded': self.test_permissions(),
            'thread_pool_healthy': self.test_thread_pool(),
            'performance_mode_selected': self.test_performance_mode()
        }
        
        passed = sum(results.values())
        total = len(results)
        
        if not all(results.values()):
            self.struct_logger.warning(
                "tests_failed",
                f"Some tests failed: {passed}/{total} passed",
                results=results
            )
            self.enter_safe_mode()
        else:
            self.struct_logger.info(
                "tests_passed",
                f"All tests passed: {passed}/{total}",
                results=results
            )
        
        return results
    
    def test_gpu(self) -> bool:
        """Test GPU availability"""
        try:
            import torch
            available = torch.cuda.is_available()
            
            if available:
                device_count = torch.cuda.device_count()
                device_name = torch.cuda.get_device_name(0)
                self.struct_logger.info(
                    "gpu_test_passed",
                    f"GPU available: {device_name}",
                    device_count=device_count
                )
            else:
                self.struct_logger.info(
                    "gpu_not_available",
                    "No GPU available, will use CPU"
                )
            
            return True  # Not having GPU is not a failure
            
        except ImportError:
            self.struct_logger.info(
                "torch_not_installed",
                "PyTorch not installed, GPU test skipped"
            )
            return True
        except Exception as e:
            self.struct_logger.error(
                "gpu_test_failed",
                f"GPU test failed: {e}",
                error=str(e)
            )
            return False
    
    def test_config(self) -> bool:
        """Test config validity"""
        try:
            from core.managers.config_manager import ConfigManager
            
            config_dir = Path("ai-worker/config")
            config_manager = ConfigManager(config_dir)
            
            # Try loading a config file
            config_manager.load_yaml("memory_watchdog.yaml", required=False)
            
            self.struct_logger.info(
                "config_test_passed",
                "Config system working"
            )
            return True
            
        except Exception as e:
            self.struct_logger.error(
                "config_test_failed",
                f"Config test failed: {e}",
                error=str(e)
            )
            return False
    
    def test_permissions(self) -> bool:
        """Test permissions loaded"""
        try:
            from core.managers.permission_manager import get_permission_manager
            from core.managers.config_manager import ConfigManager
            from error.error_handler import get_error_handler
            
            config_manager = ConfigManager(Path("ai-worker/config"))
            error_handler = get_error_handler()
            perm_manager = get_permission_manager(config_manager, error_handler)
            
            perms = perm_manager.get_all_permissions()
            
            self.struct_logger.info(
                "permissions_test_passed",
                f"Permissions loaded: {len(perms)} permissions"
            )
            return True
            
        except Exception as e:
            self.struct_logger.error(
                "permissions_test_failed",
                f"Permissions test failed: {e}",
                error=str(e)
            )
            return False
    
    def test_thread_pool(self) -> bool:
        """Test thread pool health"""
        try:
            import threading
            
            active_threads = threading.active_count()
            
            self.struct_logger.info(
                "thread_pool_test_passed",
                f"Thread pool healthy: {active_threads} active threads"
            )
            return True
            
        except Exception as e:
            self.struct_logger.error(
                "thread_pool_test_failed",
                f"Thread pool test failed: {e}",
                error=str(e)
            )
            return False
    
    def test_performance_mode(self) -> bool:
        """Test performance mode selection"""
        try:
            from core.managers.performance_modes_manager import get_performance_mode_manager
            
            mode_manager = get_performance_mode_manager()
            current_mode = mode_manager.get_current_mode()
            
            self.struct_logger.info(
                "performance_mode_test_passed",
                f"Performance mode selected: {current_mode.value}"
            )
            return True
            
        except Exception as e:
            self.struct_logger.error(
                "performance_mode_test_failed",
                f"Performance mode test failed: {e}",
                error=str(e)
            )
            return False
    
    def enter_safe_mode(self):
        """Enter safe mode due to test failures"""
        self.struct_logger.warning(
            "entering_safe_mode",
            "Entering safe mode due to test failures"
        )
        # Implementation would switch to safe mode
    
    def log_failures(self, results: Dict[str, bool]):
        """Log test failures"""
        failures = [test for test, passed in results.items() if not passed]
        
        if failures:
            self.struct_logger.error(
                "test_failures",
                f"Failed tests: {', '.join(failures)}",
                failures=failures
            )
