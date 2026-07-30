def test_health_check_endpoint(client):
    """
    Test GET /api/v1/health endpoint.
    Should return 200 OK with healthy status payload.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    data = response.get_json()
    assert data == {
        "status": "healthy",
        "service": "Propel Fault Management Backend"
    }
