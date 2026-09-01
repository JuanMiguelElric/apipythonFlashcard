from app.repositories import flashcard_repository as repo
from app.schemas.flashcard import FlashcardContent

CATEGORIA = "__test__categoria"
ALL_FIELDS = {"question", "summary", "answer", "options", "translation", "audioUrl"}


def _content(**overrides):
    base = {"question": "Pergunta", "summary": "Resumo", "answer": None, "options": None, "translation": None, "audioUrl": None}
    base.update(overrides)
    return FlashcardContent(**base)


def test_upsert_creates_flashcard_reachable_by_id(driver, next_id):
    fid, uid = next_id(), next_id()

    repo.upsert_flashcard(driver, fid, CATEGORIA, "summary", uid, _content(question="Ola"), ALL_FIELDS)

    assert repo.get_owner_user_id(driver, fid) == uid


def test_upsert_is_idempotent_merge_not_duplicate(driver, next_id):
    fid, uid = next_id(), next_id()

    repo.upsert_flashcard(driver, fid, CATEGORIA, "summary", uid, _content(question="V1"), ALL_FIELDS)
    repo.upsert_flashcard(driver, fid, CATEGORIA, "summary", uid, _content(question="V2"), ALL_FIELDS)

    result = driver.execute_query(
        "MATCH (f:flashcard {flashcard_id: $fid}) RETURN count(f) AS c, collect(f.titulo) AS titulos",
        fid=fid,
    )
    row = result.records[0]
    assert row["c"] == 1
    assert row["titulos"] == ["V2"]


def test_two_users_same_titulo_never_share_a_node(driver, next_id):
    """Caso critico do enunciado: usuario A e usuario B criam flashcards com
    o mesmo titulo ('Capital do Brasil'), flashcard_id diferentes - os dois
    devem existir como nodes independentes, sem misturar autoria."""
    fid_a, fid_b = next_id(), next_id()
    user_a, user_b = next_id(), next_id()

    repo.upsert_flashcard(driver, fid_a, CATEGORIA, "summary", user_a, _content(question="Capital do Brasil", summary="Brasilia"), ALL_FIELDS)
    repo.upsert_flashcard(driver, fid_b, CATEGORIA, "summary", user_b, _content(question="Capital do Brasil", summary="Brasilia"), ALL_FIELDS)

    result = driver.execute_query("MATCH (f:flashcard) WHERE f.titulo = 'Capital do Brasil' RETURN f.flashcard_id AS fid")
    ids = {r["fid"] for r in result.records}

    assert ids == {fid_a, fid_b}
    assert repo.get_owner_user_id(driver, fid_a) == user_a
    assert repo.get_owner_user_id(driver, fid_b) == user_b


def test_list_for_user_only_returns_own_flashcards(driver, next_id):
    fid_a, fid_b = next_id(), next_id()
    user_a, user_b = next_id(), next_id()

    repo.upsert_flashcard(driver, fid_a, CATEGORIA, "summary", user_a, _content(question="A"), ALL_FIELDS)
    repo.upsert_flashcard(driver, fid_b, CATEGORIA, "summary", user_b, _content(question="B"), ALL_FIELDS)

    groups = repo.list_for_user(driver, user_a, skip=0, limit=50)

    questions = [fc["question"] for g in groups for fc in g["flashcards"]]
    assert questions == ["A"]


def test_list_for_user_respects_pagination(driver, next_id):
    user = next_id()
    ids = [next_id() for _ in range(5)]
    for i, fid in enumerate(ids):
        repo.upsert_flashcard(driver, fid, CATEGORIA, "summary", user, _content(question=f"Q{i}"), ALL_FIELDS)

    page1 = repo.list_for_user(driver, user, skip=0, limit=2)
    page2 = repo.list_for_user(driver, user, skip=2, limit=2)

    count1 = sum(len(g["flashcards"]) for g in page1)
    count2 = sum(len(g["flashcards"]) for g in page2)
    assert count1 == 2
    assert count2 == 2


def test_update_changes_content_and_relinks_tipo(driver, next_id):
    fid, uid = next_id(), next_id()
    repo.upsert_flashcard(driver, fid, CATEGORIA, "summary", uid, _content(question="Original"), ALL_FIELDS)

    repo.update_flashcard(driver, fid, CATEGORIA, "open-ended", _content(question="Atualizado", summary=None, answer="R"), ALL_FIELDS)

    result = driver.execute_query(
        "MATCH (t:tipo)-[:TIPO_DO_FLASHCARD]->(f:flashcard {flashcard_id: $fid}) RETURN f.titulo AS titulo, f.answer AS answer, t.tipo AS tipo, count(*) AS rels",
        fid=fid,
    )
    row = result.records[0]
    assert row["titulo"] == "Atualizado"
    assert row["answer"] == "R"
    assert row["tipo"] == "open-ended"
    assert row["rels"] == 1  # relacionamento antigo (summary) foi removido, nao duplicado


def test_update_uses_standardized_relationship_names(driver, next_id):
    fid, uid = next_id(), next_id()
    repo.upsert_flashcard(driver, fid, CATEGORIA, "summary", uid, _content(question="X"), ALL_FIELDS)

    result = driver.execute_query(
        """
        MATCH (c:categoria {categoria: $categoria})-[:CATEGORIA]->(t:tipo)-[:TIPO_DO_FLASHCARD]->(f:flashcard {flashcard_id: $fid})-[:CRIADO_POR]->(u:usuario {user_id: $uid})
        RETURN count(*) AS c
        """,
        categoria=CATEGORIA,
        fid=fid,
        uid=uid,
    )
    assert result.records[0]["c"] == 1


def test_partial_update_preserves_fields_not_sent(driver, next_id):
    """Caso critico do enunciado: PUT enviando somente 'question' nao pode
    apagar summary/answer/options ja existentes no node."""
    fid, uid = next_id(), next_id()
    repo.upsert_flashcard(
        driver, fid, CATEGORIA, "multiple-choice", uid,
        _content(question="Original", summary="Resumo original", answer=None, options=[{"text": "4", "isCorrect": True}]),
        ALL_FIELDS,
    )

    repo.update_flashcard(driver, fid, CATEGORIA, "multiple-choice", _content(question="Somente pergunta mudou"), {"question"})

    stored = repo.get_content_properties(driver, fid)
    assert stored["question"] == "Somente pergunta mudou"
    assert stored["summary"] == "Resumo original"
    assert stored["options"] == [{"text": "4", "isCorrect": True}]


def test_delete_removes_node_and_reports_not_found_on_retry(driver, next_id):
    fid, uid = next_id(), next_id()
    repo.upsert_flashcard(driver, fid, CATEGORIA, "summary", uid, _content(question="X"), ALL_FIELDS)

    assert repo.delete_flashcard(driver, fid) is True
    assert repo.get_owner_user_id(driver, fid) is None
    assert repo.delete_flashcard(driver, fid) is False


def test_options_stored_as_json_string_for_laravel_compat(driver, next_id):
    fid, uid = next_id(), next_id()
    content = _content(question="2+2?", summary=None, options=[{"text": "4", "isCorrect": True}])

    repo.upsert_flashcard(driver, fid, CATEGORIA, "multiple-choice", uid, content, ALL_FIELDS)

    groups = repo.list_for_user(driver, uid, skip=0, limit=10)
    stored = groups[0]["flashcards"][0]["multiple_choice"]
    assert isinstance(stored, str)
    assert '"isCorrect": true' in stored or '"isCorrect":true' in stored
