"""
Health Dashboard API
Provides system monitoring endpoints for debugging
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
import psutil
import platform
from datetime import datetime
from pathlib import Path

from core.resource_monitor import get_monitor
from core.lazy_loader import get_lazy_loader
from core.paths import get_logs_dir

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health")
async def get_health() -> Dict[str, Any]:
    """
    Get system health status
    
    Returns:
        Health status with uptime and error counts
    """
    try:
        # Get resource monitor
        monitor = get_monitor()
        snapshot = monitor.get_snapshot()
        
        return {
            "status": "healthy" if snapshot.status == "ok" else "degraded",
            "timestamp": datetime.now().isoformat(),
            "ram_status": snapshot.status,
            "ram_percent": snapshot.ram_percent,
            "cpu_percent": snapshot.cpu_percent
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hardware")
async def get_hardware() -> Dict[str, Any]:
    """
    Get hardware information
    
    Returns:
        CPU, RAM, GPU, and platform details
    """
    try:
        mem = psutil.virtual_memory()
        cpu_count = psutil.cpu_count()
        
        # Try to detect GPU
        gpu_detected = False
        gpu_info = "None"
        
        try:
            import torch
            if torch.cuda.is_available():
                gpu_detected = True
                gpu_info = f"NVIDIA {torch.cuda.get_device_name(0)}"
        except:
            pass
        
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "processor": platform.processor(),
            "cpu_count": cpu_count,
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "ram_total_gb": round(mem.total / (1024 ** 3), 2),
            "ram_available_gb": round(mem.available / (1024 ** 3), 2),
            "ram_used_gb": round(mem.used / (1024 ** 3), 2),
            "ram_percent": mem.percent,
            "gpu_detected": gpu_detected,
            "gpu_info": gpu_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def get_models_status() -> Dict[str, Any]:
    """
    Get loaded models status
    
    Returns:
        Information about loaded and available models
    """
    try:
        loader = get_lazy_loader()
        status = loader.get_status()
        
        # Get memory usage per model (estimated)
        loaded_models = [name for name, info in status.items() if info["loaded"]]
        
        return {
            "loaded": loaded_models,
            "available": list(status.keys()),
            "status": status,
            "total_loaded": len(loaded_models)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/recent")
async def get_recent_logs(lines: int = 50) -> Dict[str, Any]:
    """
    Get recent log entries
    
    Args:
        lines: Number of recent lines to retrieve
    
    Returns:
        Recent log entries categorized by level
    """
    try:
        logs_dir = get_logs_dir()
        log_file = logs_dir / "lyra.log"
        
        if not log_file.exists():
            return {
                "errors": [],
                "warnings": [],
                "info": [],
                "total_lines": 0
            }
        
        # Read last N lines
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        # Categorize by level
        errors = [line.strip() for line in recent_lines if "ERROR" in line or "CRITICAL" in line]
        warnings = [line.strip() for line in recent_lines if "WARNING" in line]
        info = [line.strip() for line in recent_lines if "INFO" in line]
        
        return {
            "errors": errors[-10:],  # Last 10 errors
            "warnings": warnings[-10:],  # Last 10 warnings
            "info": info[-20:],  # Last 20 info messages
            "total_lines": len(recent_lines)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_system_stats() -> Dict[str, Any]:
    """
    Get comprehensive system statistics
    
    Returns:
        Detailed statistics from resource monitor
    """
    try:
        monitor = get_monitor()
        stats = monitor.get_stats()
        history = monitor.get_history(last_n=10)
        
        return {
            "current": {
                "ram_percent": history[-1].ram_percent if history else 0,
                "cpu_percent": history[-1].cpu_percent if history else 0,
                "timestamp": history[-1].timestamp.isoformat() if history else None
            },
            "statistics": stats,
            "history_count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance-mode")
async def get_performance_mode() -> Dict[str, Any]:
    """
    Get current performance mode
    
    Returns:
        Current performance mode configuration
    """
    try:
        from core.performance_manager import get_performance_manager
        
        manager = get_performance_manager()
        mode = manager.get_mode()
        
        return {
            "mode": mode.name,
            "llm_model": mode.llm_model,
            "stt_model": mode.stt_model,
            "tts_engine": mode.tts_engine,
            "vision_enabled": mode.vision_enabled,
            "expected_ram_gb": mode.expected_ram_gb,
            "recommendation": manager.get_recommendation()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
