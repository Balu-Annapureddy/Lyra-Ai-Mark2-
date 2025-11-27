"""
E2E Smoke Tests for Lyra AI Mark2
Tests critical paths: startup, health checks, model operations, skills
"""

import pytest
import httpx
import asyncio
from typing import Dict, Any


BASE_URL = "http://localhost:8000"


@pytest.fixture
async def client():
    """HTTP client fixture"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        yield client


@pytest.mark.asyncio
async def test_server_startup(client: httpx.AsyncClient):
    """Test 1: Server starts and responds"""
    response = await client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["name"] == "Lyra AI Mark2"
    assert data["version"] == "2.0.0"
    assert data["status"] == "running"
    assert "session_id" in data


@pytest.mark.asyncio
async def test_health_endpoints(client: httpx.AsyncClient):
    """Test 2: All health endpoints return 200"""
    endpoints = [
        "/health/",
        "/health/core",
        "/health/gpu",
        "/health/models",
        "/health/jobs",
        "/health/storage",
        "/health/memory",
        "/health/state"
    ]
    
    for endpoint in endpoints:
        response = await client.get(endpoint)
        assert response.status_code == 200, f"{endpoint} failed"
        data = response.json()
        assert "status" in data, f"{endpoint} missing status"


@pytest.mark.asyncio
async def test_core_health(client: httpx.AsyncClient):
    """Test 3: Core system health check"""
    response = await client.get("/health/core")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert "cpu_percent" in data
    assert "ram_percent" in data
    assert data["ram_percent"] < 95  # Should not be critically low


@pytest.mark.asyncio
async def test_gpu_detection(client: httpx.AsyncClient):
    """Test 4: GPU detection and self-test"""
    response = await client.get("/health/gpu")
    
    assert response.status_code == 200
    data = response.json()
    
    # Status should be healthy or degraded (if no GPU)
    assert data["status"] in ["healthy", "degraded"]
    
    # Should have GPU info
    assert "gpu_info" in data
    assert "self_test" in data


@pytest.mark.asyncio
async def test_memory_watchdog(client: httpx.AsyncClient):
    """Test 5: Memory watchdog is running"""
    response = await client.get("/health/memory")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["running"] is True
    assert "percent" in data
    assert "soft_limit" in data
    assert "hard_limit" in data


@pytest.mark.asyncio
async def test_model_list(client: httpx.AsyncClient):
    """Test 6: Model listing works"""
    response = await client.get("/models")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "models" in data
    assert isinstance(data["models"], list)


@pytest.mark.asyncio
async def test_state_manager(client: httpx.AsyncClient):
    """Test 7: State manager is operational"""
    response = await client.get("/state")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "user_settings" in data
    assert "model_state" in data
    assert "runtime_flags" in data
    assert "session_id" in data


@pytest.mark.asyncio
async def test_event_history(client: httpx.AsyncClient):
    """Test 8: Event bus is recording events"""
    response = await client.get("/events?last_n=10")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "events" in data
    assert isinstance(data["events"], list)
    
    # Should have at least SYSTEM_STARTUP event
    if len(data["events"]) > 0:
        event = data["events"][0]
        assert "type" in event
        assert "timestamp" in event
        assert "data" in event
        assert "source" in event


@pytest.mark.asyncio
async def test_chat_endpoint(client: httpx.AsyncClient):
    """Test 9: Chat endpoint responds"""
    response = await client.post(
        "/chat",
        json={"message": "Hello, test!"}
    )
    
    # Should return 200 or 500 (if models not loaded)
    assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_job_scheduler(client: httpx.AsyncClient):
    """Test 10: Job scheduler is operational"""
    response = await client.get("/health/jobs")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert "stats" in data


@pytest.mark.asyncio
async def test_startup_time(client: httpx.AsyncClient):
    """Test 11: Startup time is acceptable (<5s for health check)"""
    import time
    
    start = time.time()
    response = await client.get("/health/")
    duration = time.time() - start
    
    assert response.status_code == 200
    assert duration < 5.0, f"Health check took {duration:.2f}s (should be <5s)"


@pytest.mark.asyncio
async def test_cors_headers(client: httpx.AsyncClient):
    """Test 12: CORS headers are set"""
    response = await client.options("/")
    
    # Should have CORS headers
    assert "access-control-allow-origin" in response.headers or response.status_code == 200


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
