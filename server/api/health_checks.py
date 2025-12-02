"""
Comprehensive Health Check API
Provides health endpoints for all subsystems
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import psutil
from datetime import datetime

from core.gpu_manager import get_gpu_manager
from core.model_manager import get_model_manager
from core.job_scheduler import get_job_scheduler
from core.state import get_state_manager
from core.memory_watchdog import get_memory_watchdog
from core.lazy_loader import get_lazy_loader
from core.temp_manager import get_temp_manager

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Overall health check
    
    Returns:
        Health status summary
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }


@router.get("/core")
async def health_core() -> Dict[str, Any]:
    """
    Core system health
    
    Returns:
        Core system metrics
    """
    try:
        mem = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        return {
            "status": "healthy",
            "cpu_percent": cpu_percent,
            "ram_percent": mem.percent,
            "ram_available_gb": mem.available / (1024 ** 3),
            "ram_total_gb": mem.total / (1024 ** 3),
            "cpu_count": psutil.cpu_count(),
            "platform": psutil.os.name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gpu")
async def health_gpu() -> Dict[str, Any]:
    """
    GPU health check
    
    Returns:
        GPU status and self-test results
    """
    try:
        gpu_mgr = get_gpu_manager()
        status = gpu_mgr.get_status()
        
        # Run self-test
        test_results = gpu_mgr.run_self_test()
        
        return {
            "status": "healthy" if status["gpu_available"] else "degraded",
            "gpu_info": status,
            "self_test": test_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def health_models() -> Dict[str, Any]:
    """
    Model system health
    
    Returns:
        Model manager and lazy loader status
    """
    try:
        model_mgr = get_model_manager()
        lazy_loader = get_lazy_loader()
        
        models = model_mgr.list_models()
        loader_status = lazy_loader.get_status()
        disk_usage = model_mgr.get_disk_usage()
        
        installed_count = sum(1 for m in models if m["installed"])
        loaded_count = sum(1 for s in loader_status.values() if s["loaded"])
        
        return {
            "status": "healthy",
            "models_installed": installed_count,
            "models_loaded": loaded_count,
            "disk_usage_mb": disk_usage["total_mb"],
            "models": models[:5],  # First 5 models
            "loader_status": loader_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def health_jobs() -> Dict[str, Any]:
    """
    Job scheduler health
    
    Returns:
        Job scheduler statistics
    """
    try:
        scheduler = get_job_scheduler()
        stats = scheduler.get_stats()
        
        # Calculate health
        total = stats["total_jobs"]
        failed = stats["failed"]
        failure_rate = (failed / total * 100) if total > 0 else 0
        
        status = "healthy" if failure_rate < 10 else "degraded"
        
        return {
            "status": status,
            "stats": stats,
            "failure_rate": failure_rate
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/skills")
async def health_skills() -> Dict[str, Any]:
    """
    Skills system health
    
    Returns:
        Registered skills and their status
    """
    try:
        from core.agent_orchestrator import get_agent_orchestrator
        
        orchestrator = get_agent_orchestrator()
        skills = list(orchestrator.skills.keys())
        
        # Check each skill
        skill_status = {}
        for skill_name in skills:
            skill = orchestrator.skills[skill_name]
            can_execute, reason = skill.can_execute()
            skill_status[skill_name] = {
                "can_execute": can_execute,
                "reason": reason
            }
        
        healthy_count = sum(1 for s in skill_status.values() if s["can_execute"])
        
        return {
            "status": "healthy" if healthy_count == len(skills) else "degraded",
            "total_skills": len(skills),
            "healthy_skills": healthy_count,
            "skills": skill_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/storage")
async def health_storage() -> Dict[str, Any]:
    """
    Storage health check
    
    Returns:
        Disk usage and temp file statistics
    """
    try:
        temp_mgr = get_temp_manager()
        temp_stats = temp_mgr.get_stats()
        
        # Get disk usage
        disk = psutil.disk_usage('/')
        
        return {
            "status": "healthy" if disk.percent < 90 else "degraded",
            "disk_total_gb": disk.total / (1024 ** 3),
            "disk_used_gb": disk.used / (1024 ** 3),
            "disk_free_gb": disk.free / (1024 ** 3),
            "disk_percent": disk.percent,
            "temp_files": temp_stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory")
async def health_memory() -> Dict[str, Any]:
    """
    Memory watchdog health
    
    Returns:
        Memory watchdog statistics
    """
    try:
        watchdog = get_memory_watchdog()
        stats = watchdog.get_stats()
        
        status = "healthy"
        if stats["hard_limit_active"]:
            status = "critical"
        elif stats["soft_limit_active"]:
            status = "warning"
        
        return {
            "status": status,
            **stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/state")
async def health_state() -> Dict[str, Any]:
    """
    State manager health
    
    Returns:
        State manager status
    """
    try:
        state_mgr = get_state_manager()
        full_state = state_mgr.get_full_state()
        
        return {
            "status": "healthy",
            "session_id": full_state["session_id"],
            "session_duration": full_state["session_duration"],
            "models_loaded": sum(
                1 for v in full_state["model_state"].values()
                if isinstance(v, bool) and v
            )
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
