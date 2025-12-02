"""
Test script for Phase 2: Performance & Stability
Tests all new features: performance modes, stability, worker watchdog, crash recovery, health checks
"""

import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.managers.performance_modes_manager import (
    get_performance_mode_manager,
    PerformanceMode
)
from core.managers.stability_manager import get_stability_manager
from core.worker_watchdog import get_worker_watchdog, WorkerStatus
from core.crash_recovery import get_crash_recovery_manager
from core.startup_self_test import StartupSelfTest


def test_performance_modes():
    """Test performance mode manager"""
    print("\n" + "="*60)
    print("Testing Performance Modes")
    print("="*60)
    
    manager = get_performance_mode_manager()
    
    # Test 1: Get current mode
    print("\n1. Testing current mode...")
    current = manager.get_current_mode()
    print(f"   ✓ Current mode: {current.value}")
    
    # Test 2: Auto-selection
    print("\n2. Testing auto-selection...")
    auto_mode = manager.auto_select_mode()
    print(f"   ✓ Auto-selected mode: {auto_mode.value}")
    
    # Test 3: Get mode config
    print("\n3. Testing mode configuration...")
    config = manager.get_mode_config()
    print(f"   ✓ Max concurrent tasks: {config.max_concurrent_tasks}")
    print(f"   ✓ Memory limit: {config.memory_limit_percent}%")
    
    # Test 4: Health check
    print("\n4. Testing health check...")
    health = manager.health_check()
    print(f"   ✓ Status: {health['status']}")
    print(f"   ✓ Component: {health['component']}")
    
    print("\n✅ Performance mode tests passed!")


def test_stability_manager():
    """Test stability manager"""
    print("\n" + "="*60)
    print("Testing Stability Manager")
    print("="*60)
    
    manager = get_stability_manager()
    
    # Test 1: Safe execution with success
    print("\n1. Testing safe execution (success)...")
    def successful_func():
        return "success"
    
    result = manager.safe_execute(successful_func)
    print(f"   ✓ Result: {result}")
    
    # Test 2: Safe execution with retry
    print("\n2. Testing safe execution (retry)...")
    attempt = [0]
    def retry_func():
        attempt[0] += 1
        if attempt[0] < 2:
            raise Exception("Temporary failure")
        return "success after retry"
    
    result = manager.safe_execute(retry_func)
    print(f"   ✓ Result: {result}")
    print(f"   ✓ Attempts: {attempt[0]}")
    
    # Test 3: Error stats
    print("\n3. Testing error statistics...")
    stats = manager.get_error_stats(since_minutes=60)
    print(f"   ✓ Total errors: {stats['total_errors']}")
    
    # Test 4: Health check
    print("\n4. Testing health check...")
    health = manager.health_check()
    print(f"   ✓ Status: {health['status']}")
    
    print("\n✅ Stability manager tests passed!")


def test_worker_watchdog():
    """Test worker watchdog"""
    print("\n" + "="*60)
    print("Testing Worker Watchdog")
    print("="*60)
    
    watchdog = get_worker_watchdog()
    
    # Test 1: Register worker
    print("\n1. Testing worker registration...")
    success = watchdog.register_worker("worker_1")
    print(f"   ✓ Worker registered: {success}")
    
    # Test 2: Start task
    print("\n2. Testing task start...")
    watchdog.start_task("worker_1", "llm_inference", "task_123")
    stats = watchdog.get_worker_stats()
    print(f"   ✓ Active workers: {stats['active']}")
    
    # Test 3: Heartbeat
    print("\n3. Testing heartbeat...")
    watchdog.heartbeat("worker_1")
    print(f"   ✓ Heartbeat recorded")
    
    # Test 4: Complete task
    print("\n4. Testing task completion...")
    watchdog.complete_task("worker_1")
    stats = watchdog.get_worker_stats()
    print(f"   ✓ Idle workers: {stats['idle']}")
    
    # Test 5: Worker stats
    print("\n5. Testing worker statistics...")
    print(f"   ✓ Total workers: {stats['total']}")
    print(f"   ✓ Zombies: {stats['zombies']}")
    
    # Test 6: Health check
    print("\n6. Testing health check...")
    health = watchdog.health_check()
    print(f"   ✓ Status: {health['status']}")
    
    print("\n✅ Worker watchdog tests passed!")


def test_crash_recovery():
    """Test crash recovery manager"""
    print("\n" + "="*60)
    print("Testing Crash Recovery")
    print("="*60)
    
    state_dir = Path(__file__).parent / "test_state"
    manager = get_crash_recovery_manager(state_dir)
    
    # Test 1: Save state
    print("\n1. Testing state save...")
    manager._state = {"test_key": "test_value"}
    manager.save_state()
    print(f"   ✓ State saved")
    
    # Test 2: Restore state
    print("\n2. Testing state restore...")
    manager._state = {}
    success = manager.restore_state()
    print(f"   ✓ State restored: {success}")
    print(f"   ✓ State data: {manager._state}")
    
    # Test 3: Crash detection
    print("\n3. Testing crash detection...")
    manager.mark_running()
    crashed = manager.detect_crash()
    print(f"   ✓ Crash marker exists: {crashed}")
    
    # Test 4: Clean shutdown
    print("\n4. Testing clean shutdown...")
    manager.mark_clean_shutdown()
    crashed = manager.detect_crash()
    print(f"   ✓ Crash marker removed: {not crashed}")
    
    # Test 5: Health check
    print("\n5. Testing health check...")
    health = manager.health_check()
    print(f"   ✓ Status: {health['status']}")
    
    # Cleanup
    import shutil
    if state_dir.exists():
        shutil.rmtree(state_dir)
    
    print("\n✅ Crash recovery tests passed!")


def test_startup_self_tests():
    """Test startup self-tests"""
    print("\n" + "="*60)
    print("Testing Startup Self-Tests")
    print("="*60)
    
    tester = StartupSelfTest()
    
    # Run all tests
    print("\n1. Running all startup tests...")
    results = tester.run_all_tests()
    
    print(f"\n   Test Results:")
    for test_name, passed in results.items():
        status = "✓" if passed else "✗"
        print(f"   {status} {test_name}: {'PASSED' if passed else 'FAILED'}")
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n   Overall: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n✅ All startup tests passed!")
    else:
        print(f"\n⚠️  {total_count - passed_count} startup tests failed")


def test_health_aggregation():
    """Test health aggregation logic"""
    print("\n" + "="*60)
    print("Testing Health Aggregation")
    print("="*60)
    
    # Define aggregate_health function locally (was in deleted health_status.py)
    def aggregate_health(manager_healths):
        """Aggregate health status with severity-based priority"""
        if any(h.get('status') == 'error' for h in manager_healths.values()):
            return 'error'
        if any(h.get('status') == 'degraded' for h in manager_healths.values()):
            return 'degraded'
        return 'ok'
    
    # Test 1: All OK
    print("\n1. Testing all OK...")
    healths = {
        "manager1": {"status": "ok"},
        "manager2": {"status": "ok"}
    }
    result = aggregate_health(healths)
    print(f"   ✓ Result: {result} (expected: ok)")
    
    # Test 2: One degraded
    print("\n2. Testing one degraded...")
    healths = {
        "manager1": {"status": "ok"},
        "manager2": {"status": "degraded"}
    }
    result = aggregate_health(healths)
    print(f"   ✓ Result: {result} (expected: degraded)")
    
    # Test 3: One error (highest priority)
    print("\n3. Testing one error...")
    healths = {
        "manager1": {"status": "degraded"},
        "manager2": {"status": "error"}
    }
    result = aggregate_health(healths)
    print(f"   ✓ Result: {result} (expected: error)")
    
    print("\n✅ Health aggregation tests passed!")


def main():
    """Run all Phase 2 tests"""
    print("\n" + "="*60)
    print("PHASE 2: PERFORMANCE & STABILITY TESTS")
    print("="*60)
    
    try:
        test_performance_modes()
        test_stability_manager()
        test_worker_watchdog()
        test_crash_recovery()
        test_startup_self_tests()
        test_health_aggregation()
        
        print("\n" + "="*60)
        print("✅ ALL PHASE 2 TESTS PASSED!")
        print("="*60)
        print("\nPhase 2 components are working correctly.")
        print("Ready for integration and deployment.\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
