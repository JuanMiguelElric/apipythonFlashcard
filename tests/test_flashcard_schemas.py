import pytest
from pydantic import ValidationError

from app.schemas.flashcard import SubmitFlashcardRequest


def _payload(**overrides):
    base = {
        "flashcard_id": 1,
        "categoria": "Matematica",
        "tipo": "summary",
        "usuario": 5,
        "flashcard": {"question": "Capital do Brasil", "summary": "Brasilia"},
    }
    base.update(overrides)
    return base


def test_valid_payload_parses():
    data = SubmitFlashcardRequest.model_validate(_payload())

    assert data.flashcard_id == 1
    assert data.flashcard.question == "Capital do Brasil"


def test_missing_question_is_rejected():
    payload = _payload(flashcard={"summary": "Brasilia"})

    with pytest.raises(ValidationError):
        SubmitFlashcardRequest.model_validate(payload)


def test_invalid_tipo_is_rejected():
    with pytest.raises(ValidationError):
        SubmitFlashcardRequest.model_validate(_payload(tipo="nao-existe"))


def test_audio_url_accepts_data_uri_not_just_http_url():
    payload = _payload(
        tipo="audio",
        flashcard={
            "question": "Pronuncie: Hello",
            "translation": "Ola",
            "audioUrl": "data:audio/mp3;base64,AAA",
        },
    )

    data = SubmitFlashcardRequest.model_validate(payload)

    assert data.flashcard.audioUrl == "data:audio/mp3;base64,AAA"


def test_multiple_choice_options_shape():
    payload = _payload(
        tipo="multiple-choice",
        flashcard={
            "question": "2 + 2?",
            "options": [{"text": "3", "isCorrect": False}, {"text": "4", "isCorrect": True}],
        },
    )

    data = SubmitFlashcardRequest.model_validate(payload)

    assert data.flashcard.options[1].isCorrect is True


def test_flashcard_id_must_be_positive():
    with pytest.raises(ValidationError):
        SubmitFlashcardRequest.model_validate(_payload(flashcard_id=0))
