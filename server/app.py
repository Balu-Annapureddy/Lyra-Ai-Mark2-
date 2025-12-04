"""
Lyra AI Mark2 - Main Application
Integrates all Phase 1 & 2 modules into a cohesive AI OS
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Core modules
from core.logger import setup_logger

from core.state import get_state_manager
from core.gpu_manager import get_gpu_manager
from core.lazy_loader import get_lazy_loader
from core.job_scheduler import get_job_scheduler
from core.events import get_event_bus, EventType
from core.memory_watchdog import get_memory_watchdog
from core.temp_manager import get_temp_manager
from core.performance_manager import get_performance_manager
from core.agent_orchestrator import get_agent_orchestrator
from core.tracing import get_tracer
from core.model_manager import get_model_manager

# API routers
from api.health import router as health_router
from api.health_checks import router as health_checks_router

# Skills
from skills.clipboard_skill import ClipboardSkill
from skills.browser_skill import BrowserSkill
from skills.file_skill import FileSkill
from skills.scheduling_skill import SchedulingSkill
from skills.notes_skill import NotesSkill

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("=" * 60)
    logger.info("Lyra AI Mark2 - Starting...")
    logger.info("=" * 60)
    
    # Initialize core systems
    state_mgr = get_state_manager()
    event_bus = get_event_bus()
    tracer = get_tracer()
    
    # Initialize permission manager
    from core.managers.config_manager import get_config_manager
    from error.error_handler import get_error_handler
    from core.managers.permission_manager import get_permission_manager
    get_permission_manager(get_config_manager(), get_error_handler())
    
    # Start session
    state_mgr.start_session()
    
    # Publish startup event
    await event_bus.publish(
        EventType.SYSTEM_STARTUP,
        {"version": "2.0.0", "mode": "safe_startup"},
        source="app"
    )
    
    # Detect GPU
    gpu_mgr = get_gpu_manager()
    gpu_status = gpu_mgr.get_status()
    logger.info(f"GPU: {gpu_status['gpu_name']} ({gpu_status['gpu_type']})")
    
    # Run GPU self-test
    if gpu_status['gpu_available']:
        test_results = gpu_mgr.run_self_test()
        logger.info(f"GPU self-test: {len(test_results['tests_passed'])} passed, {len(test_results['tests_failed'])} failed")
    
    # Determine performance mode
    perf_mgr = get_performance_manager()
    mode = perf_mgr.get_mode()
    logger.info(f"Performance mode: {mode.name}")
    state_mgr.set_setting("performance_mode", mode.name, persist=True)
    
    # Start memory watchdog (DISABLED for low-RAM systems)
    # TODO: Re-enable with higher thresholds (95%/98%) or make configurable
    # watchdog = get_memory_watchdog()
    # 
    # # Set callbacks for memory limits
    # def soft_limit_callback(percent, mem):
    #     logger.warning(f"Soft memory limit reached: {percent:.1f}%")
    #     # Unload unused models
    #     lazy_loader = get_lazy_loader()
    #     # TODO: Implement selective unloading
    # 
    # def hard_limit_callback(percent, mem):
    #     logger.error(f"HARD memory limit reached: {percent:.1f}%")
    #     # Emergency unload all models
    #     lazy_loader = get_lazy_loader()
    #     # TODO: Implement emergency unload
    # 
    # watchdog.set_soft_limit_callback(soft_limit_callback)
    # watchdog.set_hard_limit_callback(hard_limit_callback)
    # watchdog.start()
    logger.info("Memory watchdog disabled (low-RAM system)")
    
    # Start job scheduler
    scheduler = get_job_scheduler()
    logger.info("Job scheduler ready")
    
    # Start lazy loader auto-unload
    lazy_loader = get_lazy_loader()
    lazy_loader.start_auto_unload()
    logger.info("Lazy loader auto-unload started")
    
    # Initialize agent orchestrator with skills
    orchestrator = get_agent_orchestrator()
    
    # Register skills
    skills = [
        ClipboardSkill(),
        BrowserSkill(),
        FileSkill(),
        SchedulingSkill(),
        NotesSkill()
    ]
    
    for skill in skills:
        orchestrator.register_skill(skill)
    
    logger.info(f"Registered {len(skills)} skills")
    
    # Subscribe to events (example)
    def on_model_loaded(event):
        logger.info(f"Model loaded event: {event.data}")
    
    event_bus.subscribe(EventType.MODEL_LOADED, on_model_loaded)
    
    logger.info("=" * 60)
    logger.info("Lyra AI Mark2 - Ready!")
    logger.info(f"Session ID: {state_mgr.get_session_id()}")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    
    # Publish shutdown event
    await event_bus.publish(
        EventType.SYSTEM_SHUTDOWN,
        {"session_duration": state_mgr.get_session_duration()},
        source="app"
    )
    
    # Stop subsystems
    # watchdog.stop()  # Disabled - watchdog not started
    lazy_loader.stop_auto_unload()
    await scheduler.shutdown()
    
    # Cleanup temp files
    temp_mgr = get_temp_manager()
    temp_mgr.cleanup_old_files()
    
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Lyra AI Mark2",
    description="Lightweight AI Operating System",
    version="2.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    lifespan=lifespan
)

# CORS middleware
import os

# Get allowed origins from environment or use defaults
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Production-ready CORS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(health_checks_router)

# Import and include status router
from api.status import router as status_router
app.include_router(status_router)


@app.get("/")
async def root():
    """Root endpoint"""
    state_mgr = get_state_manager()
    
    return {
        "name": "Lyra AI Mark2",
        "version": "2.0.0",
        "status": "running",
        "message": "Lyra AI Backend is running",
        "session_id": state_mgr.get_session_id(),
        "session_duration": state_mgr.get_session_duration()
    }


@app.get("/health")
async def health_check_root():
    """
    Direct health check endpoint
    Avoids 307 redirects from router prefixes
    """
    return {"status": "ok", "timestamp": "now"}


@app.get("/favicon.ico")
async def favicon():
    """
    Handle favicon requests to prevent 404s
    """
    # Return 204 No Content for now to keep logs clean
    # Alternatively, serve a static file if available
    from fastapi import Response
    return Response(status_code=204)


@app.post("/chat")
async def chat(message: dict):
    """
    Chat endpoint
    
    Body:
        {
            "message": "user message",
            "conversation_id": "optional"
        }
    """
    try:
        orchestrator = get_agent_orchestrator()
        tracer = get_tracer()
        
        user_message = message.get("message", "")
        conversation_id = message.get("conversation_id")
        
        # Trace the request
        with tracer.trace("chat_request", metadata={"message_length": len(user_message)}):
            response = await orchestrator.process_message(user_message, conversation_id)
        
        return response
    
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models")
async def list_models():
    """List available models"""
    model_mgr = get_model_manager()
    return {"models": model_mgr.list_models()}


@app.post("/models/download")
async def download_model(request: dict):
    """
    Download model
    
    Body:
        {
            "model_id": "phi-3-mini"
        }
    """
    try:
        model_mgr = get_model_manager()
        model_id = request.get("model_id")
        
        if not model_id:
            raise HTTPException(status_code=400, detail="model_id required")
        
        # Submit download job
        scheduler = get_job_scheduler()
        
        async def download_task():
            return await model_mgr.download_model(model_id)
        
        job_id = scheduler.submit_job(
            download_task,
            name=f"download_{model_id}",
            timeout=600  # 10 minutes
        )
        
        return {
            "job_id": job_id,
            "model_id": model_id,
            "status": "downloading"
        }
    
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get job status"""
    try:
        scheduler = get_job_scheduler()
        job = scheduler.get_job(job_id)
        
        return {
            "job_id": job.id,
            "name": job.name,
            "status": job.status,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error": job.error
        }
    
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/state")
async def get_state():
    """Get application state"""
    state_mgr = get_state_manager()
    return state_mgr.get_full_state()


@app.websocket("/events/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time events"""
    await websocket.accept()
    event_bus = get_event_bus()
    
    # Queue for this connection
    queue = asyncio.Queue()
    
    def event_handler(event):
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            pass
    
    # Subscribe to all events
    # Note: EventBus currently doesn't support wildcard subscription easily
    # So we'll subscribe to a few key ones or we'd need to modify EventBus
    # For now, let's modify EventBus to support wildcard or just subscribe to common ones
    
    # Better approach: The EventBus doesn't support wildcard.
    # Let's subscribe to specific important events for now.
    from core.events import EventType
    
    subscribed_events = [
        EventType.SYSTEM_STARTUP,
        EventType.SYSTEM_SHUTDOWN,
        EventType.MODEL_LOADED,
        EventType.MODEL_FAILED,
        EventType.JOB_COMPLETED,
        EventType.JOB_FAILED,
        EventType.MEMORY_WARNING
    ]
    
    for event_type in subscribed_events:
        event_bus.subscribe(event_type, event_handler)
    
    try:
        while True:
            # Wait for event
            event = await queue.get()
            
            # Send to client
            await websocket.send_json({
                "type": event.type,
                "timestamp": event.timestamp.isoformat(),
                "data": event.data,
                "source": event.source
            })
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Unsubscribe
        for event_type in subscribed_events:
            event_bus.unsubscribe(event_type, event_handler)


# Import permission manager
from core.managers.permission_manager import get_permission_manager

@app.get("/permissions")
async def list_permissions():
    """List all permissions"""
    perm_mgr = get_permission_manager()
    return {
        "permissions": perm_mgr.get_all_permissions(),
        "granted": list(perm_mgr.get_granted_permissions()),
        "denied": list(perm_mgr.get_denied_permissions())
    }

@app.post("/permissions/grant")
async def grant_permission(request: dict):
    """Grant a permission"""
    perm_mgr = get_permission_manager()
    permission = request.get("permission")
    
    if not permission:
        raise HTTPException(status_code=400, detail="permission required")
        
    try:
        perm_mgr.grant_permission(permission)
        return {"status": "granted", "permission": permission}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/permissions/revoke")
async def revoke_permission(request: dict):
    """Revoke a permission"""
    perm_mgr = get_permission_manager()
    permission = request.get("permission")
    
    if not permission:
        raise HTTPException(status_code=400, detail="permission required")
        
    try:
        perm_mgr.revoke_permission(permission)
        return {"status": "revoked", "permission": permission}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/permissions/check/{permission}")
async def check_permission(permission: str):
    """Check if a permission is granted"""
    perm_mgr = get_permission_manager()
    is_granted = perm_mgr.has_permission(permission)
    
    if not is_granted:
        raise HTTPException(status_code=403, detail=f"Permission denied: {permission}")
        
    return {"status": "granted", "permission": permission}

@app.post("/admin/test")
async def admin_test_endpoint():
    """Protected endpoint requiring file_write permission"""
    perm_mgr = get_permission_manager()
    
    # Check permission
    if not perm_mgr.has_permission("file_write"):
        raise HTTPException(status_code=403, detail="Permission denied: file_write required")
        
    return {"status": "success", "message": "Admin access granted"}


if __name__ == "__main__":
    # Setup logging
    setup_logger()
    
    # Initialize permission manager early
    from core.managers.config_manager import get_config_manager
    from error.error_handler import get_error_handler
    get_permission_manager(get_config_manager(), get_error_handler())
    
    # Run server
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
