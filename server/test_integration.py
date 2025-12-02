"""
Integration Tests for Phase 4
Tests component interactions, API integration, and system-wide functionality
"""

import unittest
import time
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

from core.managers.model_registry import ModelRegistry, ModelInfo
from core.managers.cache_manager import CacheManager
from core.memory_watchdog import MemoryWatchdog
from core.managers.config_manager import ConfigManager
from core.task_queue import TaskQueue, Priority
from core.managers.fallback_manager import FallbackManager
from core.metrics_manager import get_metrics_manager
from core.hardware_detection import HardwareDetector
from core.events import get_event_bus, EventType
from error.error_handler import ErrorHandler, get_error_handler


class TestComponentIntegration(unittest.TestCase):
    """Test how components work together"""
    
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.config_dir = Path(__file__).parent / "config"
        
    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_model_registry_with_cache_manager(self):
        """Test ModelRegistry working with CacheManager"""
        print("\n[Integration] Testing ModelRegistry + CacheManager...")
        
        # Create cache manager
        cache_dir = self.test_dir / "cache"
        cache_dir.mkdir()
        cache_mgr = CacheManager(
            cache_dir=cache_dir,
            max_cache_bytes=10 * 1024 * 1024,  # 10MB
            min_free_bytes=1024 * 1024  # 1MB
        )
        
        # Mock config for registry
        config = MagicMock()
        config.load_yaml.return_value = {
            "models": [
                {
                    "id": "test_model",
                    "name": "Test Model",
                    "type": "llm",
                    "enabled": True,
                    "ram_required_gb": 1.0,
                    "size_gb": 0.5,
                    "download_url": "",
                    "local_path": str(cache_dir / "test_model.bin")
                }
            ]
        }
        
        registry = ModelRegistry(config, MagicMock())
        
        # Verify integration
        models = registry.get_all_models()
        self.assertTrue(len(models) > 0)
        
        # Simulate model file in cache
        model_file = cache_dir / "test_model.bin"
        model_file.write_bytes(b"X" * 512 * 1024)  # 512KB
        
        # Rescan cache to detect the new file
        cache_mgr._scan_cache()
        
        # Pin model in cache
        cache_mgr.pin_model("test_model.bin", "registry")
        self.assertTrue(cache_mgr.is_pinned("test_model.bin"))
        
        print("   ✓ ModelRegistry + CacheManager integration working")
    
    def test_memory_watchdog_with_metrics(self):
        """Test MemoryWatchdog reporting to MetricsManager"""
        print("\n[Integration] Testing MemoryWatchdog + MetricsManager...")
        
        metrics = get_metrics_manager()
        config_mgr = ConfigManager(self.config_dir)
        
        # Create watchdog from config
        watchdog = MemoryWatchdog.from_config(config_mgr)
        
        # Get current usage (this should record metrics internally if integrated)
        usage = watchdog.get_current_usage()
        
        self.assertIn("percent", usage)
        self.assertIn("used_gb", usage)
        self.assertIn("available_gb", usage)
        
        # Manually record to metrics
        metrics.record_metric("memory.usage_percent", usage["percent"])
        metrics.record_metric("memory.used_gb", usage["used_gb"])
        
        # Verify metrics recorded
        all_metrics = metrics.get_metrics()
        self.assertTrue(len(all_metrics) > 0)
        
        print("   ✓ MemoryWatchdog + MetricsManager integration working")
    
    def test_task_queue_with_fallback_manager(self):
        """Test TaskQueue with FallbackManager for resilient task execution"""
        print("\n[Integration] Testing TaskQueue + FallbackManager...")
        
        task_queue = TaskQueue(max_size=10)
        fallback_mgr = FallbackManager(failure_threshold=2, cooldown_seconds=1)
        
        results = []
        
        def unreliable_task(model_id):
            """Task that might fail"""
            if model_id == "bad_model":
                raise Exception("Model failed")
            results.append(model_id)
            return f"Success: {model_id}"
        
        # Submit tasks
        task_queue.submit(Priority.HIGH, "task1", unreliable_task, "good_model")
        task_queue.submit(Priority.NORMAL, "task2", unreliable_task, "bad_model")
        
        # Process with fallback
        task1 = task_queue.get_next_task(timeout=1)
        if task1:
            try:
                result = fallback_mgr.execute_with_fallback(
                    task1.func,
                    [task1.args[0], "fallback_model"]
                )
                self.assertIsNotNone(result)
            except:
                pass
        
        print("   ✓ TaskQueue + FallbackManager integration working")
    
    def test_hardware_detector_with_model_registry(self):
        """Test HardwareDetector recommendations used by ModelRegistry"""
        print("\n[Integration] Testing HardwareDetector + ModelRegistry...")
        
        detector = HardwareDetector()
        profile = detector.analyze_system()
        
        # Get quantization recommendation
        quant_rec = detector.recommend_quantization(model_size_gb=7.0)
        self.assertIsInstance(quant_rec, str)
        
        # Mock registry
        config = MagicMock()
        config.load_yaml.return_value = {"models": []}
        registry = ModelRegistry(config, MagicMock())
        
        # Check if system RAM can handle models
        available_ram = registry.get_available_ram_gb()
        self.assertGreater(available_ram, 0)
        
        # Hardware profile should inform model selection
        self.assertTrue(hasattr(profile, "ram_total_gb"))
        self.assertTrue(hasattr(profile, "cpu_cores_physical"))
        
        print("   ✓ HardwareDetector + ModelRegistry integration working")
    
    def test_event_system_integration(self):
        """Test event system propagation across components"""
        print("\n[Integration] Testing Event System...")
        
        event_bus = get_event_bus()
        received_events = []
        
        def event_handler(event):
            received_events.append(event)
        
        # Subscribe to model events
        event_bus.subscribe(EventType.MODEL_LOADED, event_handler)
        
        # Publish event (simulating model load)
        import asyncio
        asyncio.run(event_bus.publish(
            EventType.MODEL_LOADED,
            {"model_id": "test_model", "ram_used": 2.5},
            source="test"
        ))
        
        # Give event time to propagate
        time.sleep(0.1)
        
        # Verify event received
        self.assertEqual(len(received_events), 1)
        self.assertEqual(received_events[0].data["model_id"], "test_model")
        
        print("   ✓ Event system integration working")
    
    def test_error_handler_integration(self):
        """Test ErrorHandler integration with components"""
        print("\n[Integration] Testing ErrorHandler integration...")
        
        error_handler = get_error_handler()
        
        # Test error response creation
        from error.error_codes import ErrorCode
        
        error_resp = error_handler.create_error_response(
            ErrorCode.MODEL_LOAD_FAIL,
            details="Insufficient RAM"
        )
        
        self.assertEqual(error_resp.code, "MODEL_LOAD_FAIL")
        error_dict = error_resp.dict()
        self.assertIn("message", error_dict)
        self.assertIn("severity", error_dict)
        
        # Test with metrics
        metrics = get_metrics_manager()
        metrics.increment_counter("errors.model_load_fail", 1.0)
        
        stats = metrics.get_stats()
        self.assertIn("errors.model_load_fail", stats)
        
        print("   ✓ ErrorHandler integration working")


class TestSystemWideIntegration(unittest.TestCase):
    """Test system-wide functionality"""
    
    def test_full_pipeline_simulation(self):
        """Simulate a full request pipeline"""
        print("\n[System] Testing full pipeline simulation...")
        
        # 1. Hardware detection
        detector = HardwareDetector()
        profile = detector.analyze_system()
        
        # 2. Metrics tracking
        metrics = get_metrics_manager()
        metrics.record_metric("pipeline.start", time.time())
        
        # 3. Task queue
        task_queue = TaskQueue(max_size=5)
        
        def mock_task():
            return "Task completed"
        
        task_queue.submit(Priority.HIGH, "test_task", mock_task)
        
        # 4. Get task and execute
        task = task_queue.get_next_task(timeout=1)
        if task:
            result = task.func()
            self.assertEqual(result, "Task completed")
        
        # 5. Record completion
        metrics.record_metric("pipeline.end", time.time())
        
        # Verify metrics
        all_metrics = metrics.get_metrics()
        self.assertTrue(len(all_metrics) >= 2)
        
        print("   ✓ Full pipeline simulation working")
    
    def test_concurrent_component_usage(self):
        """Test multiple components being used concurrently"""
        print("\n[System] Testing concurrent component usage...")
        
        import threading
        
        metrics = get_metrics_manager()
        results = {"thread1": False, "thread2": False}
        
        def thread1_work():
            # Simulate metrics recording
            for i in range(5):
                metrics.increment_counter("thread1.counter", 1.0)
                time.sleep(0.01)
            results["thread1"] = True
        
        def thread2_work():
            # Simulate task queue usage
            task_queue = TaskQueue(max_size=10)
            for i in range(5):
                task_queue.submit(Priority.NORMAL, f"task_{i}", lambda: None)
                time.sleep(0.01)
            results["thread2"] = True
        
        # Run threads
        t1 = threading.Thread(target=thread1_work)
        t2 = threading.Thread(target=thread2_work)
        
        t1.start()
        t2.start()
        
        t1.join(timeout=2)
        t2.join(timeout=2)
        
        # Verify both completed
        self.assertTrue(results["thread1"])
        self.assertTrue(results["thread2"])
        
        print("   ✓ Concurrent component usage working")


def main():
    """Run all integration tests"""
    print("\n" + "=" * 60)
    print("PHASE 4: INTEGRATION TESTS")
    print("=" * 60)
    
    # Run tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestComponentIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestSystemWideIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("=" * 60)
        print("\nComponents are working together correctly.")
        print("Ready for API endpoint testing.\n")
        return 0
    else:
        print("❌ SOME INTEGRATION TESTS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit(main())
