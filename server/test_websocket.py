"""
WebSocket Integration Tests
Tests real-time event streaming via WebSockets
"""

import pytest
from fastapi.testclient import TestClient
from app import app
from core.events import get_event_bus, EventType
import asyncio

# Use TestClient for WebSocket testing
# Note: TestClient uses httpx under the hood and supports ASGI websockets

def test_websocket_connection():
    """Test WebSocket connection establishment"""
    client = TestClient(app)
    with client.websocket_connect("/events/ws") as websocket:
        # Connection should be successful
        pass

def test_websocket_event_streaming():
    """Test receiving events over WebSocket"""
    # We need to run the app in a way that allows background tasks (EventBus)
    # TestClient runs the app in the same thread, so we can use it.
    
    client = TestClient(app)
    event_bus = get_event_bus()
    
    with client.websocket_connect("/events/ws") as websocket:
        # Publish an event
        event_bus.publish_sync(
            EventType.MODEL_LOADED,
            {"model_id": "test_model", "status": "ready"},
            source="test_websocket"
        )
        
        # Receive event
        data = websocket.receive_json()
        
        assert data["type"] == EventType.MODEL_LOADED
        assert data["data"]["model_id"] == "test_model"
        assert data["source"] == "test_websocket"

def test_websocket_multiple_events():
    """Test receiving multiple events"""
    client = TestClient(app)
    event_bus = get_event_bus()
    
    with client.websocket_connect("/events/ws") as websocket:
        # Publish multiple events
        event_bus.publish_sync(
            EventType.SYSTEM_STARTUP,
            {"version": "2.0.0"},
            source="test"
        )
        
        event_bus.publish_sync(
            EventType.MEMORY_WARNING,
            {"percent": 85.0},
            source="monitor"
        )
        
        # Receive events
        msg1 = websocket.receive_json()
        assert msg1["type"] == EventType.SYSTEM_STARTUP
        
        msg2 = websocket.receive_json()
        assert msg2["type"] == EventType.MEMORY_WARNING

def test_websocket_disconnection():
    """Test clean disconnection"""
    client = TestClient(app)
    with client.websocket_connect("/events/ws") as websocket:
        websocket.close()
        # Should not raise exception
