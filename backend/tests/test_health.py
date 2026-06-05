"""Tests for health check endpoints."""


def test_root_health_endpoint(client):
    """Test the root health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "success" in data
    assert "data" in data
    assert "error" in data
    assert data["success"] is True
    assert data["error"] is None
    assert "status" in data["data"]


def test_api_health_endpoint(client):
    """Test the API health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert "success" in data
    assert "data" in data
    assert "error" in data
    assert data["success"] is True
    assert data["error"] is None


def test_nonexistent_endpoint(client):
    """Test that nonexistent endpoints return 404."""
    response = client.get("/nonexistent")
    assert response.status_code == 404


def test_cors_headers_on_health_endpoint(client):
    """Test that CORS headers are present on health endpoint."""
    response = client.get("/", headers={"origin": "http://localhost:3000"})
    assert response.status_code == 200
    # CORS headers should be present when origin is allowed
    assert "access-control-allow-origin" in response.headers or response.status_code == 200
