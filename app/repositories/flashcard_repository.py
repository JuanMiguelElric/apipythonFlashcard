import json

from neo4j import Driver, RoutingControl

# Mapeia campo do payload (FlashcardContent) -> propriedade armazenada no
# node :flashcard. Usado para montar um SET dinamico que toca somente os
# campos realmente enviados no payload - ver _content_set_params.
_CONTENT_FIELD_TO_PROPERTY = {
    "question": "titulo",
    "summary": "descricao",
    "answer": "answer",
    "options": "multiple_choice",
    "translation": "translation",
    "audioUrl": "audio_url",
}


def get_owner_user_id(driver: Driver, flashcard_id: int, database: str = "neo4j") -> int | None:
    result = driver.execute_query(
        """
        MATCH (f:flashcard {flashcard_id: $flashcard_id})-[:CRIADO_POR]->(u:usuario)
        RETURN u.user_id AS user_id
        """,
        flashcard_id=flashcard_id,
        routing_=RoutingControl.READ,
        database_=database,
    )
    if not result.records:
        return None
    return result.records[0]["user_id"]


def get_content_properties(driver: Driver, flashcard_id: int, database: str = "neo4j") -> dict | None:
    """Le o conteudo persistido de fato (nao o que veio no request) - usado
    para responder create/update com o estado real do node, que pode
    divergir do payload quando o update foi parcial (campos omitidos
    preservam o valor anterior em vez de virar null)."""
    result = driver.execute_query(
        """
        MATCH (f:flashcard {flashcard_id: $flashcard_id})
        RETURN f.titulo AS question, f.descricao AS summary, f.answer AS answer,
               f.multiple_choice AS multiple_choice, f.translation AS translation,
               f.audio_url AS audioUrl
        """,
        flashcard_id=flashcard_id,
        routing_=RoutingControl.READ,
        database_=database,
    )
    if not result.records:
        return None
    record = result.records[0]
    multiple_choice = record["multiple_choice"]
    return {
        "question": record["question"],
        "summary": record["summary"],
        "answer": record["answer"],
        "options": json.loads(multiple_choice) if multiple_choice else None,
        "translation": record["translation"],
        "audioUrl": record["audioUrl"],
    }


def upsert_flashcard(
    driver: Driver,
    flashcard_id: int,
    categoria: str,
    tipo: str,
    usuario: int,
    content,
    provided_fields: set[str],
    database: str = "neo4j",
) -> None:
    content_params = _content_set_params(content, provided_fields)
    set_clause = _build_set_clause("f", content_params)
    driver.execute_query(
        f"""
        MERGE (c:categoria {{categoria: $categoria}})
        MERGE (t:tipo {{tipo: $tipo, categoria: $categoria}})
        MERGE (u:usuario {{user_id: $usuario}})
        MERGE (f:flashcard {{flashcard_id: $flashcard_id}})
        {set_clause}
        MERGE (c)-[:CATEGORIA]->(t)
        MERGE (t)-[:TIPO_DO_FLASHCARD]->(f)
        MERGE (f)-[:CRIADO_POR]->(u)
        """,
        flashcard_id=flashcard_id,
        categoria=categoria,
        tipo=tipo,
        usuario=usuario,
        database_=database,
        **content_params,
    )


def update_flashcard(
    driver: Driver,
    flashcard_id: int,
    categoria: str,
    tipo: str,
    content,
    provided_fields: set[str],
    database: str = "neo4j",
) -> None:
    content_params = _content_set_params(content, provided_fields)
    set_clause = _build_set_clause("f", content_params)
    driver.execute_query(
        f"""
        MATCH (f:flashcard {{flashcard_id: $flashcard_id}})
        OPTIONAL MATCH (:tipo)-[old_rel:TIPO_DO_FLASHCARD]->(f)
        DELETE old_rel
        MERGE (c:categoria {{categoria: $categoria}})
        MERGE (t:tipo {{tipo: $tipo, categoria: $categoria}})
        MERGE (c)-[:CATEGORIA]->(t)
        MERGE (t)-[:TIPO_DO_FLASHCARD]->(f)
        {set_clause}
        """,
        flashcard_id=flashcard_id,
        categoria=categoria,
        tipo=tipo,
        database_=database,
        **content_params,
    )


def delete_flashcard(driver: Driver, flashcard_id: int, database: str = "neo4j") -> bool:
    result = driver.execute_query(
        """
        MATCH (f:flashcard {flashcard_id: $flashcard_id})
        WITH f, count(f) AS found
        DETACH DELETE f
        RETURN found
        """,
        flashcard_id=flashcard_id,
        database_=database,
    )
    return bool(result.records) and result.records[0]["found"] > 0


def list_for_user(driver: Driver, user_id: int, skip: int, limit: int, database: str = "neo4j") -> list[dict]:
    result = driver.execute_query(
        """
        MATCH (u:usuario {user_id: $user_id})<-[:CRIADO_POR]-(f:flashcard)
              <-[:TIPO_DO_FLASHCARD]-(t:tipo)<-[:CATEGORIA]-(c:categoria)
        WITH c, t, u, f
        ORDER BY f.flashcard_id
        SKIP $skip LIMIT $limit
        WITH c, t, u, collect({
            flashcard_id: f.flashcard_id,
            question: f.titulo,
            summary: f.descricao,
            answer: f.answer,
            multiple_choice: f.multiple_choice,
            translation: f.translation,
            audioUrl: f.audio_url
        }) AS flashcards
        RETURN c.categoria AS categoria, t.tipo AS tipo, u.user_id AS usuario, flashcards
        ORDER BY categoria, tipo
        """,
        user_id=user_id,
        skip=skip,
        limit=limit,
        routing_=RoutingControl.READ,
        database_=database,
    )
    return [
        {
            "categoria": record["categoria"],
            "tipo": record["tipo"],
            "usuario": record["usuario"],
            "flashcards": record["flashcards"],
        }
        for record in result.records
    ]


def _content_set_params(content, provided_fields: set[str]) -> dict:
    params = {}
    for field, prop in _CONTENT_FIELD_TO_PROPERTY.items():
        if field not in provided_fields:
            continue
        value = getattr(content, field)
        if field == "options":
            value = _options_to_json(value)
        params[prop] = value
    return params


def _build_set_clause(node_alias: str, params: dict) -> str:
    if not params:
        return ""
    assignments = ",\n            ".join(f"{node_alias}.{prop} = ${prop}" for prop in params)
    return f"SET {assignments}"


def _options_to_json(options) -> str | None:
    if options is None:
        return None
    # Neo4j nao aceita lista de mapas como propriedade de node - precisa
    # ser serializada. O Laravel (FlashcardService::mergeContent) espera
    # de volta exatamente essa string via json_decode, entao o formato de
    # armazenamento e o formato de leitura precisam ficar acoplados.
    return json.dumps([option.model_dump() for option in options])
