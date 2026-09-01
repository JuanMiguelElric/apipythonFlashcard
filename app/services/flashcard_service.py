from neo4j import Driver

from app.errors import ConflictError, ForbiddenError, NotFoundError
from app.repositories import flashcard_repository as repo
from app.schemas.flashcard import SubmitFlashcardRequest, UpdateFlashcardRequest


def submit(driver: Driver, data: SubmitFlashcardRequest, database: str = "neo4j") -> dict:
    existing_owner = repo.get_owner_user_id(driver, data.flashcard_id, database)
    if existing_owner is not None and existing_owner != data.usuario:
        raise ConflictError(
            "flashcard_id ja pertence a outro usuario.",
            details={"flashcard_id": data.flashcard_id},
        )

    repo.upsert_flashcard(
        driver,
        data.flashcard_id,
        data.categoria,
        data.tipo,
        data.usuario,
        data.flashcard,
        data.flashcard.model_fields_set,
        database,
    )

    return _present(driver, data.flashcard_id, data.categoria, data.tipo, data.usuario, database)


def update(driver: Driver, flashcard_id: int, data: UpdateFlashcardRequest, database: str = "neo4j") -> dict:
    existing_owner = repo.get_owner_user_id(driver, flashcard_id, database)
    if existing_owner is None:
        raise NotFoundError("Flashcard nao encontrado.", details={"flashcard_id": flashcard_id})
    if existing_owner != data.usuario:
        raise ForbiddenError(
            "Usuario nao e proprietario deste flashcard.",
            details={"flashcard_id": flashcard_id},
        )

    repo.update_flashcard(
        driver,
        flashcard_id,
        data.categoria,
        data.tipo,
        data.flashcard,
        data.flashcard.model_fields_set,
        database,
    )

    return _present(driver, flashcard_id, data.categoria, data.tipo, data.usuario, database)


def delete(driver: Driver, flashcard_id: int, usuario: int, database: str = "neo4j") -> None:
    existing_owner = repo.get_owner_user_id(driver, flashcard_id, database)
    if existing_owner is None:
        raise NotFoundError("Flashcard nao encontrado.", details={"flashcard_id": flashcard_id})
    if existing_owner != usuario:
        raise ForbiddenError(
            "Usuario nao e proprietario deste flashcard.",
            details={"flashcard_id": flashcard_id},
        )

    repo.delete_flashcard(driver, flashcard_id, database)


def list_for_user(
    driver: Driver, user_id: int, page: int, per_page: int, max_page_size: int, database: str = "neo4j"
) -> list[dict]:
    limit = min(per_page, max_page_size)
    skip = (page - 1) * limit
    return repo.list_for_user(driver, user_id, skip, limit, database)


def _present(driver: Driver, flashcard_id: int, categoria: str, tipo: str, usuario: int, database: str) -> dict:
    # Le o estado real persistido em vez de ecoar o payload recebido: num
    # update parcial, os campos omitidos do request continuam com o valor
    # anterior no node, e a resposta precisa refletir isso (nao pode dizer
    # que um campo virou null quando na verdade foi preservado).
    content = repo.get_content_properties(driver, flashcard_id, database)
    return {
        "flashcard_id": flashcard_id,
        "categoria": categoria,
        "tipo": tipo,
        "usuario": usuario,
        "flashcard": content,
    }
