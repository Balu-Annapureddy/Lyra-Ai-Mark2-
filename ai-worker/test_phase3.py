import unittest
import time
import shutil
import tempfile
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

from core.hardware_detection import HardwareDetector
from core.metrics_manager import get_metrics_manager
from core.managers.cache_manager import CacheManager
from core.task_queue import TaskQueue, Priority
from core.managers.fallback_manager import FallbackManager
from core.voice_pipeline import VoicePipeline
from core.managers.model_registry import ModelRegistry, ModelInfo
from core.managers.config_manager import ConfigManager
from error.error_handler import ErrorHandler

class TestPhase3(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.metrics = get_metrics_manager()
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_hardware_detection(self):
        detector = HardwareDetector()
        profile = detector.analyze_system()
        
        self.assertTrue(hasattr(profile, "cpu_cores_physical"))
        self.assertTrue(hasattr(profile, "ram_total_gb"))
        self.assertTrue(hasattr(profile, "gpu_available"))
        
        # Test quantization recommendation
        rec = detector.recommend_quantization(model_size_gb=10.0)
        self.assertIsInstance(rec, str)

    def test_metrics_manager(self):
        self.metrics.increment_counter("test_counter", 1, {"tag": "val"})
        self.metrics.record_metric("test_gauge", 42.0)
        self.metrics.record_time("test_timer", 0.5)
        
        # Verify history
        metrics = self.metrics.get_metrics()
        self.assertTrue(len(metrics) >= 3)
        
        # Verify aggregation
        stats = self.metrics.get_stats()
        self.assertIn("test_counter", stats)
        self.assertEqual(stats["test_counter"]["count"], 1.0)

    def test_cache_manager(self):
        cache_dir = self.test_dir / "cache"
        cache_dir.mkdir()
        
        # Create dummy files
        (cache_dir / "model_a.bin").write_bytes(b"A" * 1024) # 1KB
        (cache_dir / "model_b.bin").write_bytes(b"B" * 1024) # 1KB
        
        cm = CacheManager(
            cache_dir=cache_dir,
            max_cache_bytes=1600, # ~1.5KB, enough for 1 file but not 2
            min_free_bytes=0
        )
        
        # Pin model A
        cm.pin_model("model_a.bin", "user_request")
        self.assertTrue(cm.is_pinned("model_a.bin"))
        
        # Ensure space for new file (should evict unpinned B if needed, but B is already there)
        # Let's try to add model C
        (cache_dir / "model_c.bin").write_bytes(b"C" * 1024)
        
        # This should trigger eviction of B (unpinned) to fit C + A (pinned)
        # Note: ensure_space checks existing files too
        cm.ensure_space(1024) 
        
        # Verify B is gone (or at least A is kept)
        # Actually, ensure_space is called BEFORE writing.
        # Let's simulate:
        # Current usage: A(1KB) + B(1KB) + C(1KB) = 3KB. Max = 1.5KB.
        # A is pinned. B and C are not.
        # If we run ensure_space, it should evict unpinned files.
        
        cm._scan_cache() # Update usage
        cm.ensure_space(0) # Just enforce limit
        
        self.assertTrue((cache_dir / "model_a.bin").exists()) # Pinned
        # B or C should be evicted. Since both accessed same time, arbitrary.
        # But A MUST exist.

    def test_task_queue(self):
        tq = TaskQueue(max_size=5)
        
        # Submit tasks
        results = []
        def task_func(val):
            results.append(val)
            
        tq.submit(Priority.NORMAL, "t1", task_func, 1)
        tq.submit(Priority.HIGH, "t2", task_func, 2)
        
        # Verify priority order (High before Normal)
        item1 = tq.get_next_task(timeout=1)
        item2 = tq.get_next_task(timeout=1)
        
        self.assertEqual(item1.args[0], 2) # High
        self.assertEqual(item2.args[0], 1) # Normal
        
        # Test Backpressure
        for i in range(10):
            tq.submit(Priority.LOW, f"flood_{i}", task_func, i)
            
        # Should reject some
        self.assertTrue(tq.qsize() <= 5)

    def test_fallback_manager(self):
        fm = FallbackManager(failure_threshold=2, cooldown_seconds=1)
        
        mock_func = MagicMock(side_effect=[Exception("Fail"), "Success"])
        
        # First call fails, second succeeds (fallback logic handles retry/next model)
        # But execute_with_fallback switches models.
        
        def test_op(model_id):
            if model_id == "bad":
                raise Exception("Fail")
            return "ok"
            
        res = fm.execute_with_fallback(test_op, ["bad", "good"])
        self.assertEqual(res, "ok")
        
        # Test circuit breaker
        # Fail "bad" twice
        try: fm.execute_with_fallback(test_op, ["bad"]) 
        except: pass
        try: fm.execute_with_fallback(test_op, ["bad"]) 
        except: pass
        
        # Now "bad" should be open (skipped)
        # We need to mock logger to verify "circuit_open" or check internal state
        self.assertTrue(fm._is_circuit_open("bad"))

    def test_model_registry_atomic(self):
        # Mock dependencies
        config = MagicMock()
        config.load_yaml.return_value = {"models": [{"id": "m1", "enabled": True, "ram_required_gb": 1.0, "type": "llm", "name": "M1", "size_gb": 1.0, "download_url": "", "local_path": ""}]}
        
        registry = ModelRegistry(config, MagicMock())
        
        # Mock internal methods to avoid real sleep/load
        registry._load_weights = MagicMock(return_value="model_obj")
        registry._safe_warmup = MagicMock(return_value=True)
        registry._swap_active_model = MagicMock()
        
        # Test atomic load
        model = registry.load_model_atomic("m1")
        
        self.assertEqual(model, "model_obj")
        registry._load_weights.assert_called()
        registry._safe_warmup.assert_called()
        registry._swap_active_model.assert_called()

    def test_voice_pipeline(self):
        vp = VoicePipeline()
        vp.start()
        
        # Push audio
        vp.push_audio(b"audio")
        
        # We can't easily test the async processing without mocking everything,
        # but we can check if it accepts data and doesn't crash.
        time.sleep(0.1)
        
        vp.stop()

if __name__ == '__main__':
    unittest.main()
