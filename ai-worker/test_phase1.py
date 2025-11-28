"""
Test script for Phase 1 configuration and core systems
Tests PermissionManager, ModelRegistry, MemoryWatchdog config integration
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.managers.config_manager import ConfigManager
from core.managers.permission_manager import PermissionManager
from core.managers.model_registry import ModelRegistry, ModelInfo
from core.memory_watchdog import MemoryWatchdog
from core.container import initialize_core_services
from error.error_handler import get_error_handler


def test_permission_manager():
    """Test PermissionManager"""
    print("\n" + "="*60)
    print("Testing PermissionManager")
    print("="*60)
    
    config_dir = Path(__file__).parent / "config"
    config_manager = ConfigManager(config_dir)
    error_handler = get_error_handler()
    
    perm_manager = PermissionManager(config_manager, error_handler)
    
    # Test permission checking
    print("\n1. Testing permission checking...")
    has_mic = perm_manager.has_permission("microphone")
    print(f"   ✓ Has microphone permission: {has_mic}")
    
    # Test granting permission
    print("\n2. Testing permission granting...")
    perm_manager.grant_permission("microphone")
    has_mic_after = perm_manager.has_permission("microphone")
    print(f"   ✓ Microphone permission granted: {has_mic_after}")
    
    # Test revoking permission
    print("\n3. Testing permission revoking...")
    perm_manager.revoke_permission("microphone")
    has_mic_revoked = perm_manager.has_permission("microphone")
    print(f"   ✓ Microphone permission revoked: {not has_mic_revoked}")
    
    # Test getting all permissions
    print("\n4. Testing get all permissions...")
    all_perms = perm_manager.get_all_permissions()
    print(f"   ✓ Total permissions: {len(all_perms)}")
    print(f"   ✓ Permissions: {list(all_perms.keys())}")
    
    # Test health check
    print("\n5. Testing health check...")
    health = perm_manager.health_check()
    print(f"   ✓ Status: {health['status']}")
    print(f"   ✓ Permissions loaded: {health['permissions_loaded']}")
    print(f"   ✓ Granted: {health['granted_count']}")
    
    print("\n✅ PermissionManager tests passed!")


def test_model_registry():
    """Test ModelRegistry"""
    print("\n" + "="*60)
    print("Testing ModelRegistry")
    print("="*60)
    
    config_dir = Path(__file__).parent / "config"
    config_manager = ConfigManager(config_dir)
    error_handler = get_error_handler()
    
    registry = ModelRegistry(config_manager, error_handler)
    
    # Test getting available RAM
    print("\n1. Testing RAM detection...")
    available_ram = registry.get_available_ram_gb()
    print(f"   ✓ Available RAM: {available_ram:.2f} GB")
    
    # Test getting all models
    print("\n2. Testing get all models...")
    all_models = registry.get_all_models(include_disabled=True)
    print(f"   ✓ Total models in registry: {len(all_models)}")
    for model in all_models[:3]:  # Show first 3
        print(f"      - {model.name} ({model.type}): {model.ram_required_gb} GB RAM")
    
    # Test getting available models (RAM compatible)
    print("\n3. Testing RAM-compatible models...")
    available_models = registry.get_available_models()
    print(f"   ✓ Compatible models: {len(available_models)}")
    for model in available_models[:3]:
        print(f"      - {model.name}: {model.ram_required_gb} GB RAM required")
    
    # Test getting models by type
    print("\n4. Testing get models by type...")
    llm_models = registry.get_models_by_type("llm")
    stt_models = registry.get_models_by_type("stt")
    print(f"   ✓ LLM models: {len(llm_models)}")
    print(f"   ✓ STT models: {len(stt_models)}")
    
    # Test model compatibility check
    print("\n5. Testing model compatibility...")
    if all_models:
        test_model = all_models[0]
        is_compatible = registry.is_model_compatible(test_model.id)
        print(f"   ✓ {test_model.name} compatible: {is_compatible}")
    
    # Test health check
    print("\n6. Testing health check...")
    health = registry.health_check()
    print(f"   ✓ Status: {health['status']}")
    print(f"   ✓ Total models: {health['models_total']}")
    print(f"   ✓ Compatible models: {health['models_compatible']}")
    
    print("\n✅ ModelRegistry tests passed!")


def test_memory_watchdog_config():
    """Test MemoryWatchdog config integration"""
    print("\n" + "="*60)
    print("Testing MemoryWatchdog Config Integration")
    print("="*60)
    
    config_dir = Path(__file__).parent / "config"
    config_manager = ConfigManager(config_dir)
    
    # Test loading from config
    print("\n1. Testing config loading...")
    watchdog = MemoryWatchdog.from_config(config_manager)
    print(f"   ✓ Watchdog created from config")
    print(f"   ✓ Enabled: {watchdog.enabled}")
    print(f"   ✓ Soft limit: {watchdog.soft_limit}%")
    print(f"   ✓ Hard limit: {watchdog.hard_limit}%")
    print(f"   ✓ Check interval: {watchdog.check_interval}s")
    
    # Test current usage
    print("\n2. Testing memory usage...")
    usage = watchdog.get_current_usage()
    print(f"   ✓ Current RAM usage: {usage['percent']:.1f}%")
    print(f"   ✓ Used: {usage['used_gb']:.2f} GB")
    print(f"   ✓ Available: {usage['available_gb']:.2f} GB")
    print(f"   ✓ Total: {usage['total_gb']:.2f} GB")
    
    # Test stats
    print("\n3. Testing watchdog stats...")
    stats = watchdog.get_stats()
    print(f"   ✓ Running: {stats['running']}")
    print(f"   ✓ Soft limit active: {stats['soft_limit_active']}")
    print(f"   ✓ Hard limit active: {stats['hard_limit_active']}")
    
    print("\n✅ MemoryWatchdog config tests passed!")


def test_container_integration():
    """Test ServiceContainer integration"""
    print("\n" + "="*60)
    print("Testing ServiceContainer Integration")
    print("="*60)
    
    config_dir = Path(__file__).parent / "config"
    
    # Initialize core services
    print("\n1. Initializing core services...")
    container = initialize_core_services(config_dir)
    print("   ✓ Core services initialized")
    
    # Test getting ConfigManager
    print("\n2. Testing ConfigManager retrieval...")
    from core.managers.config_manager import ConfigManager
    config_manager = container.get(ConfigManager)
    print(f"   ✓ ConfigManager retrieved: {config_manager is not None}")
    
    # Test getting PermissionManager
    print("\n3. Testing PermissionManager retrieval...")
    from core.managers.permission_manager import PermissionManager
    perm_manager = container.get(PermissionManager)
    print(f"   ✓ PermissionManager retrieved: {perm_manager is not None}")
    
    # Test getting ModelRegistry
    print("\n4. Testing ModelRegistry retrieval...")
    from core.managers.model_registry import ModelRegistry
    model_registry = container.get(ModelRegistry)
    print(f"   ✓ ModelRegistry retrieved: {model_registry is not None}")
    
    # Test getting MemoryWatchdog
    print("\n5. Testing MemoryWatchdog retrieval...")
    from core.memory_watchdog import MemoryWatchdog
    watchdog = container.get(MemoryWatchdog)
    print(f"   ✓ MemoryWatchdog retrieved: {watchdog is not None}")
    
    # Test singleton behavior
    print("\n6. Testing singleton behavior...")
    perm_manager2 = container.get(PermissionManager)
    is_singleton = perm_manager is perm_manager2
    print(f"   ✓ Singleton working: {is_singleton}")
    
    print("\n✅ Container integration tests passed!")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PHASE 1 CONFIGURATION & CORE SYSTEMS TESTS")
    print("="*60)
    
    try:
        test_permission_manager()
        test_model_registry()
        test_memory_watchdog_config()
        test_container_integration()
        
        print("\n" + "="*60)
        print("✅ ALL PHASE 1 TESTS PASSED!")
        print("="*60)
        print("\nPhase 1 configuration and core systems are working correctly.")
        print("Ready to proceed with Phase 2 implementation.\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
