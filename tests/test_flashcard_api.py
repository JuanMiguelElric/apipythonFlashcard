from unittest.mock import patch

CATEGORIA = "__test__categoria_api"


def _submit_payload(fid, uid, **overrides):
    base = {
        "flashcard_id": fid,
        "categoria": CATEGORIA,
        "tipo": "summary",
        "usuario": uid,
        "flashcard": {"question": "Capital do Brasil", "summary": "Brasilia"},
    }
    base.update(overrides)
    return base


def test_create_flashcard_returns_201_with_stable_id(client, auth_headers, next_id):
    fid, uid = next_id(), next_id()

    response = client.post("/submit_flash", json=_submit_payload(fid, uid), headers=auth_headers)

    assert response.status_code == 201
    body = response.get_json()
    assert body["flashcard_id"] == fid
    assert body["flashcard"]["question"] == "Capital do Brasil"


def test_create_with_invalid_payload_returns_400_with_field_details(client, auth_headers, next_id):
    payload = _submit_payload(next_id(), next_id())
    del payload["flashcard"]["question"]

    response = client.post("/submit_flash", json=payload, headers=auth_headers)

    assert response.status_code == 400
    body = response.get_json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert any("question" in d["field"] for d in body["error"]["details"])


def test_create_with_flashcard_id_owned_by_another_user_is_conflict(client, auth_headers, next_id):
    fid, user_a, user_b = next_id(), next_id(), next_id()
    client.post("/submit_flash", json=_submit_payload(fid, user_a), headers=auth_headers)

    response = client.post("/submit_flash", json=_submit_payload(fid, user_b), headers=auth_headers)

    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "OWNERSHIP_CONFLICT"


def test_index_requires_user_id_and_filters_by_it(client, auth_headers, next_id):
    fid_a, fid_b, user_a, user_b = next_id(), next_id(), next_id(), next_id()
    client.post("/submit_flash", json=_submit_payload(fid_a, user_a, flashcard={"question": "A", "summary": "a"}), headers=auth_headers)
    client.post("/submit_flash", json=_submit_payload(fid_b, user_b, flashcard={"question": "B", "summary": "b"}), headers=auth_headers)

    missing_param = client.get("/flashcard/index", headers=auth_headers)
    assert missing_param.status_code == 400

    response = client.get(f"/flashcard/index?user_id={user_a}", headers=auth_headers)
    assert response.status_code == 200
    groups = response.get_json()
    questions = [fc["question"] for g in groups for fc in g["flashcards"]]
    assert questions == ["A"]


def test_index_uses_configured_default_page_size_when_per_page_omitted(client, auth_headers, next_id, app):
    user = next_id()
    for i in range(3):
        client.post(
            "/submit_flash",
            json=_submit_payload(next_id(), user, flashcard={"question": f"Q{i}", "summary": "s"}),
            headers=auth_headers,
        )

    default_page_size = app.config["DEFAULT_PAGE_SIZE"]
    response = client.get(f"/flashcard/index?user_id={user}", headers=auth_headers)

    assert response.status_code == 200
    assert default_page_size >= 3  # sanity: config default is large enough that nothing is truncated in this test
    groups = response.get_json()
    questions = [fc["question"] for g in groups for fc in g["flashcards"]]
    assert len(questions) == 3


def test_update_existing_flashcard(client, auth_headers, next_id):
    fid, uid = next_id(), next_id()
    client.post("/submit_flash", json=_submit_payload(fid, uid), headers=auth_headers)

    response = client.put(
        f"/flashcard/{fid}",
        json={"categoria": CATEGORIA, "tipo": "summary", "usuario": uid, "flashcard": {"question": "Atualizada", "summary": "Novo"}},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.get_json()["flashcard"]["question"] == "Atualizada"


def test_partial_update_preserves_fields_not_sent_in_request(client, auth_headers, next_id):
    """Caso critico do enunciado: PUT enviando somente 'question' nao pode
    apagar summary/answer/options ja existentes no flashcard."""
    fid, uid = next_id(), next_id()
    client.post(
        "/submit_flash",
        json=_submit_payload(
            fid,
            uid,
            tipo="multiple-choice",
            flashcard={
                "question": "Pergunta original",
                "summary": "Resumo original",
                "options": [{"text": "4", "isCorrect": True}],
            },
        ),
        headers=auth_headers,
    )

    response = client.put(
        f"/flashcard/{fid}",
        json={
            "categoria": CATEGORIA,
            "tipo": "multiple-choice",
            "usuario": uid,
            "flashcard": {"question": "Somente a pergunta mudou"},
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    flashcard = response.get_json()["flashcard"]
    assert flashcard["question"] == "Somente a pergunta mudou"
    assert flashcard["summary"] == "Resumo original"
    assert flashcard["options"] == [{"text": "4", "isCorrect": True}]


def test_update_by_non_owner_is_forbidden(client, auth_headers, next_id):
    fid, owner, other = next_id(), next_id(), next_id()
    client.post("/submit_flash", json=_submit_payload(fid, owner), headers=auth_headers)

    response = client.put(
        f"/flashcard/{fid}",
        json={"categoria": CATEGORIA, "tipo": "summary", "usuario": other, "flashcard": {"question": "Invasao"}},
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "FORBIDDEN"


def test_update_nonexistent_flashcard_returns_404(client, auth_headers, next_id):
    fid, uid = next_id(), next_id()

    response = client.put(
        f"/flashcard/{fid}",
        json={"categoria": CATEGORIA, "tipo": "summary", "usuario": uid, "flashcard": {"question": "X"}},
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "NOT_FOUND"


def test_delete_existing_and_then_missing_flashcard(client, auth_headers, next_id):
    fid, uid = next_id(), next_id()
    client.post("/submit_flash", json=_submit_payload(fid, uid), headers=auth_headers)

    first = client.delete(f"/flashcard/{fid}", json={"usuario": uid}, headers=auth_headers)
    second = client.delete(f"/flashcard/{fid}", json={"usuario": uid}, headers=auth_headers)

    assert first.status_code == 204
    assert second.status_code == 404


def test_delete_by_non_owner_is_forbidden(client, auth_headers, next_id):
    fid, owner, other = next_id(), next_id(), next_id()
    client.post("/submit_flash", json=_submit_payload(fid, owner), headers=auth_headers)

    response = client.delete(f"/flashcard/{fid}", json={"usuario": other}, headers=auth_headers)

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "FORBIDDEN"


def test_unexpected_error_returns_generic_500_without_internal_details(client, auth_headers, next_id):
    fid, uid = next_id(), next_id()

    with patch("app.services.flashcard_service.repo.get_owner_user_id", side_effect=RuntimeError("boom: senha=Taran@2603")):
        response = client.post("/submit_flash", json=_submit_payload(fid, uid), headers=auth_headers)

    assert response.status_code == 500
    body = response.get_json()
    assert body == {"error": {"code": "INTERNAL_ERROR", "message": "Nao foi possivel processar a solicitacao."}}
    assert "senha" not in response.get_data(as_text=True)
    assert "boom" not in response.get_data(as_text=True)
