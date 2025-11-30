"""
CORS Integration Tests
Tests Cross-Origin Resource Sharing configuration
"""

import pytest
from fastapi.testclient import TestClient
from app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_cors_preflight_request(client):
    """Test CORS preflight (OPTIONS) request"""
    response = client.options(
        "/",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type"
        }
    )
    
    # Should return 200 for OPTIONS
    assert response.status_code == 200
    
    # Should have CORS headers
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers


def test_cors_simple_request(client):
    """Test simple CORS request from allowed origin"""
    response = client.get(
        "/",
        headers={"Origin": "http://localhost:5173"}
    )
    
    assert response.status_code == 200
    
    # Should have CORS header
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] in [
        "http://localhost:5173",
        "*"
    ]


def test_cors_vite_origin(client):
    """Test CORS with Vite dev server origin"""
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:5173"}
    )
    
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_cors_react_origin(client):
    """Test CORS with React dev server origin"""
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"}
    )
    
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_cors_credentials(client):
    """Test CORS with credentials"""
    response = client.get(
        "/",
        headers={
            "Origin": "http://localhost:5173",
            "Cookie": "session=test"
        }
    )
    
    assert response.status_code == 200
    # Should allow credentials
    assert "access-control-allow-credentials" in response.headers


def test_cors_post_request(client):
    """Test CORS with POST request"""
    # Use /chat endpoint which is more straightforward
    response = client.post(
        "/chat",
        json={"message": "test"},
        headers={"Origin": "http://localhost:5173"}
    )
    
    # Should work (200 or 500 depending on orchestrator state)
    assert response.status_code in [200, 500]
    assert "access-control-allow-origin" in response.headers
