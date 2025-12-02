"""
System Status API Endpoint
Provides comprehensive system monitoring and health information
"""

from fastapi import APIRouter
from typing import Dict, Any
import psutil
import time
from datetime import datetime

from core.state import get_state_manager
from core.gpu_manager import get_gpu_manager
from core.memory_watchdog import get_memory_watchdog
from core.metrics_manager import get_metrics_manager
from core.hardware_detection import HardwareDetector
from core.task_queue import TaskQueue
from core.performance_manager import get_performance_manager

router = APIRouter(prefix="/status", tags=["status"])


@router.get("")
async def get_system_status() -> Dict[str, Any]:
    """
    Get comprehensive system status
    
    Returns detailed information about:
    - System resources (CPU, RAM, GPU)
    - Component health
    - Active tasks
    - Performance metrics
    - Session information
    - Warnings and alerts
    - Fallback/error counters
    - Cache insights
    """
    
    state_mgr = get_state_manager()
    
    # System resources
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # GPU status
    try:
        gpu_mgr = get_gpu_manager()
        gpu_status = gpu_mgr.get_status()
    except:
        gpu_status = {
            "gpu_available": False,
            "gpu_name": "None",
            "gpu_type": "none"
        }
    
    # Memory watchdog
    try:
        watchdog = get_memory_watchdog()
        watchdog_stats = watchdog.get_stats()
    except:
        watchdog_stats = {
            "running": False,
            "soft_limit_active": False,
            "hard_limit_active": False
        }
    
    # Metrics
    try:
        metrics_mgr = get_metrics_manager()
        recent_metrics = metrics_mgr.get_metrics()
        metrics_stats = metrics_mgr.get_stats()
    except:
        recent_metrics = []
        metrics_stats = {}
    
    # Hardware profile
    try:
        detector = HardwareDetector()
        hw_profile = detector.analyze_system()
        hardware_info = {
            "cpu_cores_physical": hw_profile.cpu_cores_physical,
            "cpu_cores_logical": hw_profile.cpu_cores_logical,
            "ram_total_gb": hw_profile.ram_total_gb,
            "ram_available_gb": hw_profile.ram_available_gb,
            "gpu_available": hw_profile.gpu_available,
            "gpu_name": hw_profile.gpu_name
        }
    except:
        hardware_info = {
            "cpu_cores_physical": psutil.cpu_count(logical=False),
            "cpu_cores_logical": psutil.cpu_count(logical=True),
            "ram_total_gb": round(memory.total / (1024**3), 2),
            "ram_available_gb": round(memory.available / (1024**3), 2),
            "gpu_available": False,
            "gpu_name": "Unknown"
        }
    
    # Performance mode
    try:
        perf_mgr = get_performance_manager()
        perf_mode = perf_mgr.get_mode().name
        perf_config = perf_mgr.get_mode_config()
        performance_info = {
            "mode": perf_mode,
            "max_concurrent_tasks": perf_config.max_concurrent_tasks,
            "memory_limit_percent": perf_config.memory_limit_percent
        }
    except:
        performance_info = {
            "mode": "unknown",
            "max_concurrent_tasks": 0,
            "memory_limit_percent": 0
        }
    
    # ===== NEW: Warnings Detection =====
    warnings = []
    
    # High CPU warning
    if cpu_percent > 85:
        warnings.append(f"CPU usage above 85% ({cpu_percent:.1f}%)")
    
    # High RAM warning
    if memory.percent > 85:
        warnings.append(f"RAM usage above 85% ({memory.percent:.1f}%)")
    
    # Cache capacity warning
    try:
        from core.managers.cache_manager import get_cache_manager
        cache_mgr = get_cache_manager()
        cache_usage = cache_mgr.get_current_usage()
        cache_max = cache_mgr.max_cache_bytes
        cache_percent = (cache_usage / cache_max * 100) if cache_max > 0 else 0
        
        if cache_percent > 90:
            warnings.append(f"Cache at {cache_percent:.1f}% capacity")
    except:
        cache_percent = 0
        cache_usage = 0
        cache_max = 0
    
    # Slow task detection
    slow_task_count = 0
    try:
        # Check recent metrics for slow tasks (>5s execution time)
        for metric in recent_metrics[-100:]:  # Last 100 metrics
            if metric.get("name") == "task_duration" and metric.get("value", 0) > 5.0:
                slow_task_count += 1
        
        if slow_task_count > 0:
            warnings.append(f"Slow tasks detected: {slow_task_count}")
    except:
        pass
    
    # Memory watchdog warnings
    if watchdog_stats.get("soft_limit_active"):
        warnings.append("Memory soft limit active")
    if watchdog_stats.get("hard_limit_active"):
        warnings.append("Memory HARD limit active - emergency cleanup")
    
    # ===== NEW: Fallback / Error Counters =====
    fallbacks = {
        "model_failover": int(metrics_mgr.get_counter_value("model_failover")),
        "cache_evictions": int(metrics_mgr.get_counter_value("cache_eviction")),
        "job_retries": int(metrics_mgr.get_counter_value("job_retry")),
        "websocket_disconnects": int(metrics_mgr.get_counter_value("websocket_disconnect"))
    }
    
    # ===== NEW: Cache Insights =====
    try:
        from core.managers.cache_manager import get_cache_manager
        cache_mgr = get_cache_manager()
        
        # Get cache items
        cache_items = cache_mgr._items if hasattr(cache_mgr, '_items') else {}
        
        # Find largest model
        largest_model = "None"
        largest_size = 0
        for path_str, item in cache_items.items():
            if item.size_bytes > largest_size:
                largest_size = item.size_bytes
                largest_model = item.path.name if hasattr(item.path, 'name') else str(item.path)
        
        # Calculate hit/miss ratio (placeholder - would need actual tracking)
        # For now, use a simple heuristic based on cache evictions
        total_accesses = metrics_mgr.get_counter_value("cache_access") or 100
        cache_hits = total_accesses - fallbacks["cache_evictions"]
        hit_ratio = (cache_hits / total_accesses) if total_accesses > 0 else 0.0
        
        cache_insights = {
            "size_mb": round(cache_usage / (1024**2), 2),
            "capacity_mb": round(cache_max / (1024**2), 2),
            "usage_percent": round(cache_percent, 1),
            "evictions": fallbacks["cache_evictions"],
            "largest_model": largest_model,
            "largest_model_mb": round(largest_size / (1024**2), 2),
            "hit_ratio": round(hit_ratio, 2),
            "total_items": len(cache_items)
        }
    except Exception as e:
        cache_insights = {
            "size_mb": 0,
            "capacity_mb": 0,
            "usage_percent": 0,
            "evictions": 0,
            "largest_model": "Unknown",
            "largest_model_mb": 0,
            "hit_ratio": 0.0,
            "total_items": 0,
            "error": str(e)
        }
    
    return {
        "status": "running",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        
        # Session info
        "session": {
            "session_id": state_mgr.get_session_id(),
            "uptime_seconds": state_mgr.get_session_duration(),
            "started_at": state_mgr.get_session_start_time().isoformat() if hasattr(state_mgr, 'get_session_start_time') else None
        },
        
        # System resources
        "resources": {
            "cpu": {
                "usage_percent": cpu_percent,
                "cores_physical": hardware_info["cpu_cores_physical"],
                "cores_logical": hardware_info["cpu_cores_logical"]
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "usage_percent": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "usage_percent": disk.percent
            },
            "gpu": gpu_status
        },
        
        # Hardware profile
        "hardware": hardware_info,
        
        # Performance mode
        "performance": performance_info,
        
        # Component health
        "components": {
            "memory_watchdog": {
                "running": watchdog_stats.get("running", False),
                "soft_limit_active": watchdog_stats.get("soft_limit_active", False),
                "hard_limit_active": watchdog_stats.get("hard_limit_active", False)
            },
            "metrics_manager": {
                "total_metrics": len(recent_metrics),
                "stats_count": len(metrics_stats)
            }
        },
        
        # Recent metrics summary
        "metrics_summary": {
            "total_recorded": len(recent_metrics),
            "stats": metrics_stats
        },
        
        # ===== NEW SECTIONS =====
        
        # Warnings and alerts
        "warnings": warnings,
        
        # Fallback and error counters
        "fallbacks": fallbacks,
        
        # Cache insights
        "cache": cache_insights
    }



@router.get("/health")
async def get_status_health() -> Dict[str, str]:
    """Quick health check for status endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
