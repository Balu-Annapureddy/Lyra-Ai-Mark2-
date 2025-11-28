"""
Health and Status API Endpoints
Provides comprehensive system health and status monitoring
"""

from fastapi import APIRouter
from typing import Dict, Any
import psutil
from datetime import datetime
import time

from core.container import get_container
from core.managers.config_manager import ConfigManager
from core.managers.permission_manager import PermissionManager
from core.managers.model_registry import ModelRegistry
from core.memory_watchdog import MemoryWatchdog
from core.managers.performance_modes_manager import get_performance_mode_manager
from core.managers.stability_manager import get_stability_manager
from core.worker_watchdog import get_worker_watchdog
from core.crash_recovery import get_crash_recovery_manager
from core.structured_logger import get_structured_logger


router = APIRouter()
struct_logger = get_structured_logger("HealthStatusAPI")

# Track app start time for uptime
_app_start_time = time.time()

# Track task metrics
_task_metrics = {
    "completed": 0,
    "durations": [],
    "slowdowns": []
}


def aggregate_health(manager_healths: Dict) -> str:
    """
    Aggregate health status with severity-based priority
    Priority order: error > degraded > ok
    
    Args:
        manager_healths: Dictionary of manager health checks
        
    Returns:
        Overall health status
    """
    if any(h.get('status') == 'error' for h in manager_healths.values()):
        return 'error'
    if any(h.get('status') == 'degraded' for h in manager_healths.values()):
        return 'degraded'
    return 'ok'


@router.get("/health/managers")
async def get_managers_health() -> Dict[str, Any]:
    """
    Get health status from all managers
    
    Returns:
        Aggregated health status
    """
    container = get_container()
    managers_health = {}
    
    # Config Manager
    try:
        if container.has(ConfigManager):
            config_manager = container.get(ConfigManager)
            managers_health["config_manager"] = {
                "status": "ok",
                "component": "ConfigManager"
            }
    except Exception as e:
        managers_health["config_manager"] = {"status": "error", "error": str(e)}
    
    # Permission Manager
    try:
        if container.has(PermissionManager):
            perm_manager = container.get(PermissionManager)
            managers_health["permission_manager"] = perm_manager.health_check()
    except Exception as e:
        managers_health["permission_manager"] = {"status": "error", "error": str(e)}
    
    # Model Registry
    try:
        if container.has(ModelRegistry):
            registry = container.get(ModelRegistry)
            managers_health["model_registry"] = registry.health_check()
    except Exception as e:
        managers_health["model_registry"] = {"status": "error", "error": str(e)}
    
    # Memory Watchdog
    try:
        if container.has(MemoryWatchdog):
            watchdog = container.get(MemoryWatchdog)
            stats = watchdog.get_stats()
            managers_health["memory_watchdog"] = {
                "status": "ok",
                "component": "MemoryWatchdog",
                "details": stats
            }
    except Exception as e:
        managers_health["memory_watchdog"] = {"status": "error", "error": str(e)}
    
    # Performance Mode Manager
    try:
        mode_manager = get_performance_mode_manager()
        managers_health["performance_mode"] = mode_manager.health_check()
    except Exception as e:
        managers_health["performance_mode"] = {"status": "error", "error": str(e)}
    
    # Stability Manager
    try:
        stability = get_stability_manager()
        managers_health["stability_manager"] = stability.health_check()
    except Exception as e:
        managers_health["stability_manager"] = {"status": "error", "error": str(e)}
    
    # Worker Watchdog
    try:
        worker_watchdog = get_worker_watchdog()
        managers_health["worker_watchdog"] = worker_watchdog.health_check()
    except Exception as e:
        managers_health["worker_watchdog"] = {"status": "error", "error": str(e)}
    
    # Crash Recovery
    try:
        crash_recovery = get_crash_recovery_manager()
        managers_health["crash_recovery"] = crash_recovery.health_check()
    except Exception as e:
        managers_health["crash_recovery"] = {"status": "error", "error": str(e)}
    
    # Aggregate overall health
    overall_health = aggregate_health(managers_health)
    
    return {
        "status": overall_health,
        "timestamp": datetime.utcnow().isoformat(),
        "managers": managers_health,
        "overall_health": overall_health
    }


def calculate_memory_pressure() -> str:
    """
    Calculate memory pressure level
    
    Returns:
        Pressure level: none, low, moderate, high, critical
    """
    mem = psutil.virtual_memory()
    percent = mem.percent
    
    if percent < 50:
        return "none"
    elif percent < 65:
        return "low"
    elif percent < 80:
        return "moderate"
    elif percent < 90:
        return "high"
    else:
        return "critical"


@router.get("/status")
async def get_system_status() -> Dict[str, Any]:
    """
    Get comprehensive system status with performance warnings
    
    Returns:
        System status dictionary
    """
    # Calculate uptime
    uptime = int(time.time() - _app_start_time)
    
    # Get memory info
    mem = psutil.virtual_memory()
    memory_pressure = calculate_memory_pressure()
    
    # Get performance mode
    try:
        mode_manager = get_performance_mode_manager()
        current_mode = mode_manager.get_current_mode().value
    except:
        current_mode = "unknown"
    
    # Get worker stats
    try:
        worker_watchdog = get_worker_watchdog()
        worker_stats = worker_watchdog.get_worker_stats()
    except:
        worker_stats = {"total": 0, "active": 0, "idle": 0, "zombies": 0}
    
    # Get model info
    try:
        container = get_container()
        if container.has(ModelRegistry):
            registry = container.get(ModelRegistry)
            models_loaded = []  # Would get from actual model manager
            models_available = len(registry.models)
            models_compatible = len(registry.get_available_models())
        else:
            models_loaded = []
            models_available = 0
            models_compatible = 0
    except:
        models_loaded = []
        models_available = 0
        models_compatible = 0
    
    # Calculate task metrics
    avg_duration = 0
    if _task_metrics["durations"]:
        avg_duration = sum(_task_metrics["durations"]) / len(_task_metrics["durations"])
    
    # Generate warnings
    warnings = []
    if memory_pressure in ["high", "critical"]:
        warnings.append(f"High memory pressure detected ({mem.percent:.1f}%)")
    if worker_stats.get("zombies", 0) > 0:
        warnings.append(f"{worker_stats['zombies']} zombie workers detected")
    if memory_pressure == "critical":
        warnings.append("Critical memory pressure - models may be unloaded")
    
    return {
        "uptime": uptime,
        "performance_mode": current_mode,
        "memory": {
            "total_gb": round(mem.total / (1024 ** 3), 2),
            "used_gb": round(mem.used / (1024 ** 3), 2),
            "available_gb": round(mem.available / (1024 ** 3), 2),
            "percent": round(mem.percent, 1),
            "pressure": memory_pressure
        },
        "models": {
            "loaded": models_loaded,
            "available": models_available,
            "compatible": models_compatible
        },
        "workers": {
            "active": worker_stats.get("active", 0),
            "idle": worker_stats.get("idle", 0),
            "total": worker_stats.get("total", 0),
            "zombies": worker_stats.get("zombies", 0)
        },
        "tasks": {
            "pending": 0,  # Would get from task queue
            "running": worker_stats.get("active", 0),
            "completed": _task_metrics["completed"],
            "avg_duration_ms": int(avg_duration),
            "slowdowns": _task_metrics["slowdowns"][-5:]  # Last 5 slowdowns
        },
        "warnings": warnings
    }


@router.get("/health/core")
async def get_core_health() -> Dict[str, Any]:
    """
    Get core system health (from Phase 1)
    
    Returns:
        Core health status
    """
    from core.health_check import get_core_health_check
    
    health_checker = get_core_health_check()
    return health_checker.get_health()
