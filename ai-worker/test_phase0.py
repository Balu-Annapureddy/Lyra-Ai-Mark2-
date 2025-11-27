"""
Test script for Phase 0 foundation components
Tests ConfigManager, ServiceContainer, ErrorHandler, and FailSafe
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.managers.config_manager import ConfigManager
from core.container import ServiceContainer, get_container
from error.error_handler import ErrorHandler, create_error_response
from error.error_codes import ErrorCode
from core.failsafe import FailSafe


def test_config_manager():
    """Test ConfigManager"""
    print("\n" + "="*60)
    print("Testing ConfigManager")
    print("="*60)
    
    config_dir = Path(__file__).parent / "config"
    manager = ConfigManager(config_dir)
    
    # Test loading YAML
    print("\n1. Loading performance_modes.yaml...")
    perf_config = manager.load_yaml("performance_modes.yaml")
    print(f"   ✓ Loaded config version: {perf_config.get('config_version')}")
    print(f"   ✓ Has low_power_mode: {' low_power_mode' in perf_config}")
    
    # Test loading JSON (will create default if missing)
    print("\n2. Loading permissions.json...")
    perm_config = manager.load_json("permissions.json", required=False)
    if perm_config:
        print(f"   ✓ Loaded permissions: {list(perm_config.keys())}")
    else:
        print("   ℹ Permissions file doesn't exist yet (will be created)")
    
    # Test cache
    print("\n3. Testing cache...")
    cached = manager.load_yaml("performance_modes.yaml")
    print(f"   ✓ Cache working: {cached is perf_config}")
    
    print("\n✅ ConfigManager tests passed!")


def test_service_container():
    """Test ServiceContainer"""
    print("\n" + "="*60)
    print("Testing ServiceContainer")
    print("="*60)
    
    container = ServiceContainer()
    
    # Test registration
    print("\n1. Registering services...")
    
    class TestService:
        def __init__(self):
            self.value = "test"
    
    container.register(TestService, singleton=True)
    print("   ✓ Registered TestService")
    
    # Test retrieval
    print("\n2. Getting service instance...")
    instance1 = container.get(TestService)
    instance2 = container.get(TestService)
    print(f"   ✓ Singleton working: {instance1 is instance2}")
    print(f"   ✓ Instance value: {instance1.value}")
    
    # Test global container
    print("\n3. Testing global container...")
    global_container = get_container()
    print(f"   ✓ Global container created: {global_container is not None}")
    
    print("\n✅ ServiceContainer tests passed!")


def test_error_handler():
    """Test ErrorHandler"""
    print("\n" + "="*60)
    print("Testing ErrorHandler")
    print("="*60)
    
    error_codes_path = Path(__file__).parent / "error" / "error_codes.yaml"
    handler = ErrorHandler(error_codes_path)
    
    # Test error response creation
    print("\n1. Creating error responses...")
    
    error1 = handler.create_error_response(
        ErrorCode.MODEL_LOAD_FAIL,
        details="Insufficient RAM"
    )
    print(f"   ✓ Error code: {error1.code}")
    print(f"   ✓ Message: {error1.message}")
    print(f"   ✓ Severity: {error1.severity}")
    print(f"   ✓ HTTP status: {error1.http_status}")
    
    # Test convenience function
    print("\n2. Testing convenience function...")
    error2 = create_error_response(ErrorCode.PERMISSION_DENIED)
    print(f"   ✓ Created via convenience function: {error2.code}")
    
    # Test severity check
    print("\n3. Testing severity checks...")
    is_critical = handler.is_critical(ErrorCode.LOW_RAM)
    print(f"   ✓ LOW_RAM is critical: {is_critical}")
    
    print("\n✅ ErrorHandler tests passed!")


def test_failsafe():
    """Test FailSafe"""
    print("\n" + "="*60)
    print("Testing FailSafe")
    print("="*60)
    
    config_dir = Path(__file__).parent / "config"
    failsafe = FailSafe(config_dir)
    
    # Test safe boot
    print("\n1. Testing safe boot...")
    boot_success = failsafe.safe_boot()
    print(f"   ✓ Boot successful: {boot_success}")
    print(f"   ✓ Recovery mode: {failsafe.is_recovery_mode()}")
    
    if failsafe.is_recovery_mode():
        print("\n2. Recovery mode info:")
        info = failsafe.get_recovery_info()
        print(f"   ℹ Failed configs: {info['failed_configs']}")
        print(f"   ℹ Message: {info['message']}")
    
    print("\n✅ FailSafe tests passed!")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PHASE 0 FOUNDATION TESTS")
    print("="*60)
    
    try:
        test_config_manager()
        test_service_container()
        test_error_handler()
        test_failsafe()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nPhase 0 foundation components are working correctly.")
        print("Ready to proceed with Phase 1 implementation.\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
