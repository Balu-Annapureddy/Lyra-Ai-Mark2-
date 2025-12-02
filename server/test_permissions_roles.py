"""
Permissions & Roles Integration Tests
Tests RBAC functionality and permission enforcement
"""

import pytest
from fastapi.testclient import TestClient
from app import app
from core.managers.permission_manager import get_permission_manager

@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client

def test_list_permissions(client):
    """Test listing permissions"""
    response = client.get("/permissions")
    assert response.status_code == 200
    data = response.json()
    assert "permissions" in data
    assert "granted" in data
    assert "denied" in data
    assert "file_write" in data["permissions"]

def test_permission_enforcement(client):
    """Test permission enforcement on protected endpoint"""
    # First revoke permission to ensure it fails
    client.post("/permissions/revoke", json={"permission": "file_write"})
    
    # Try to access protected endpoint
    response = client.post("/admin/test")
    assert response.status_code == 403
    assert "Permission denied" in response.json()["detail"]
    
    # Grant permission
    client.post("/permissions/grant", json={"permission": "file_write"})
    
    # Try again
    response = client.post("/admin/test")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_check_permission_endpoint(client):
    """Test check permission endpoint"""
    # Grant
    client.post("/permissions/grant", json={"permission": "camera"})
    
    response = client.get("/permissions/check/camera")
    assert response.status_code == 200
    
    # Revoke
    client.post("/permissions/revoke", json={"permission": "camera"})
    
    response = client.get("/permissions/check/camera")
    assert response.status_code == 403

def test_invalid_permission(client):
    """Test handling of invalid permissions"""
    response = client.post("/permissions/grant", json={"permission": "invalid_perm"})
    assert response.status_code == 400
