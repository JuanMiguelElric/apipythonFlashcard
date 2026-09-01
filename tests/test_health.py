def test_health_returns_ok_without_auth(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "neo4j": "up"}
