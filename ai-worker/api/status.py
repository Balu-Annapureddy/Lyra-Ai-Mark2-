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
        }
    }


@router.get("/health")
async def get_status_health() -> Dict[str, str]:
    """Quick health check for status endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
