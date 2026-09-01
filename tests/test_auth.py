def test_submit_without_token_is_rejected(client):
    response = client.post("/submit_flash", json={})

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_submit_with_wrong_token_is_rejected(client):
    response = client.post("/submit_flash", json={}, headers={"X-Service-Token": "token-errado"})

    assert response.status_code == 401


def test_index_without_token_is_rejected(client):
    response = client.get("/flashcard/index?user_id=1")

    assert response.status_code == 401


def test_update_and_delete_without_token_are_rejected(client):
    assert client.put("/flashcard/1", json={}).status_code == 401
    assert client.delete("/flashcard/1").status_code == 401
