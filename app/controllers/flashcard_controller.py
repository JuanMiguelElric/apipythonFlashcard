from flask import current_app, jsonify, request
from pydantic import ValidationError

from app.database import get_database, get_driver
from app.errors import ValidationAppError
from app.schemas.flashcard import DeleteFlashcardRequest, IndexQueryParams, SubmitFlashcardRequest, UpdateFlashcardRequest
from app.services import flashcard_service


def _parse(model_cls, payload):
    try:
        return model_cls.model_validate(payload)
    except ValidationError as exc:
        raise ValidationAppError(
            "Payload invalido.",
            details=[{"field": ".".join(str(p) for p in e["loc"]), "message": e["msg"]} for e in exc.errors()],
        ) from exc


def submit():
    data = _parse(SubmitFlashcardRequest, request.get_json(silent=True) or {})
    result = flashcard_service.submit(get_driver(), data, get_database())
    return jsonify(result), 201


def update(flashcard_id: int):
    data = _parse(UpdateFlashcardRequest, request.get_json(silent=True) or {})
    result = flashcard_service.update(get_driver(), flashcard_id, data, get_database())
    return jsonify(result), 200


def destroy(flashcard_id: int):
    data = _parse(DeleteFlashcardRequest, request.get_json(silent=True) or {})
    flashcard_service.delete(get_driver(), flashcard_id, data.usuario, get_database())
    return "", 204


def index():
    params = _parse(IndexQueryParams, request.args.to_dict())
    per_page = params.per_page or current_app.config["DEFAULT_PAGE_SIZE"]
    result = flashcard_service.list_for_user(
        get_driver(),
        params.user_id,
        params.page,
        per_page,
        current_app.config["MAX_PAGE_SIZE"],
        get_database(),
    )
    return jsonify(result), 200
