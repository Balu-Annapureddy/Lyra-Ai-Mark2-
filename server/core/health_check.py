"""
Core Health Check Aggregator
Aggregates health checks from all managers into a single endpoint
"""

from typing import Dict, Any, Optional
from datetime import datetime
import psutil

from core.container import get_container
from core.managers.config_manager import ConfigManager
from core.managers.permission_manager import PermissionManager
from core.managers.model_registry import ModelRegistry
from core.memory_watchdog import MemoryWatchdog
from core.managers.model_download_manager import get_download_manager
from core.structured_logger import get_structured_logger


class CoreHealthCheck:
    """
    Aggregates health checks from all core managers
    
    Provides /health/core endpoint data
    """
    
    def __init__(self):
        """Initialize health check aggregator"""
        self.struct_logger = get_structured_logger("CoreHealthCheck")
        self.container = get_container()
    
    def get_health(self) -> Dict[str, Any]:
        """
        Get comprehensive health check for all core systems
        
        Returns:
            Dictionary with health status for all managers
        """
        health_data = {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }
        
        # System info
        try:
            mem = psutil.virtual_memory()
            health_data["system"] = {
                "ram_total_gb": round(mem.total / (1024**3), 2),
                "ram_available_gb": round(mem.available / (1024**3), 2),
                "ram_used_percent": mem.percent,
                "cpu_count": psutil.cpu_count()
            }
        except Exception as e:
            self.struct_logger.error(
                "system_health_failed",
                f"Failed to get system health: {e}"
            )
            health_data["system"] = {"error": str(e)}
        
        # Memory Watchdog
        try:
            if self.container.has(MemoryWatchdog):
                watchdog = self.container.get(MemoryWatchdog)
                stats = watchdog.get_stats()
                health_data["components"]["memory_watchdog"] = {
                    "enabled": watchdog.enabled,
                    "running": stats["running"],
                    "soft_limit": stats["soft_limit"],
                    "hard_limit": stats["hard_limit"],
                    "current_usage_percent": stats["percent"],
                    "soft_limit_active": stats["soft_limit_active"],
                    "hard_limit_active": stats["hard_limit_active"]
                }
        except Exception as e:
            health_data["components"]["memory_watchdog"] = {"error": str(e)}
        
        # Permission Manager
        try:
            if self.container.has(PermissionManager):
                perm_manager = self.container.get(PermissionManager)
                perm_health = perm_manager.health_check()
                health_data["components"]["permission_manager"] = {
                    "status": perm_health["status"],
                    "loaded_permissions": perm_health["permissions_loaded"],
                    "granted_count": perm_health["granted_count"],
                    "denied_count": perm_health["denied_count"]
                }
        except Exception as e:
            health_data["components"]["permission_manager"] = {"error": str(e)}
        
        # Model Registry
        try:
            if self.container.has(ModelRegistry):
                registry = self.container.get(ModelRegistry)
                registry_health = registry.health_check()
                health_data["components"]["model_registry"] = {
                    "status": registry_health["status"],
                    "models_total": registry_health["models_total"],
                    "models_enabled": registry_health["models_enabled"],
                    "models_compatible": registry_health["models_compatible"],
                    "available_ram_gb": registry_health["available_ram_gb"]
                }
        except Exception as e:
            health_data["components"]["model_registry"] = {"error": str(e)}
        
        # Model Download Manager (stub)
        try:
            download_manager = get_download_manager(None)  # Get existing instance
            download_health = download_manager.health_check()
            health_data["components"]["model_download_manager"] = download_health
        except Exception:
            # Not initialized yet, skip
            pass
        
        # Check if any component has errors
        has_errors = any(
            "error" in comp
            for comp in health_data["components"].values()
        )
        
        if has_errors:
            health_data["status"] = "degraded"
        
        return health_data


# Singleton instance
_health_check: Optional[CoreHealthCheck] = None


def get_core_health_check() -> CoreHealthCheck:
    """Get or create the global health check instance"""
    global _health_check
    if _health_check is None:
        _health_check = CoreHealthCheck()
    return _health_check
