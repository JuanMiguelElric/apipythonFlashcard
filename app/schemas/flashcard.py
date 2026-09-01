from typing import Literal, Optional

from pydantic import BaseModel, Field

# Valores fixos pelo StoreFlashcardRequest::rules() do Laravel
# (app/Http/Requests/StoreFlashcardRequest.php). Qualquer novo tipo precisa
# ser adicionado nos dois lados em conjunto.
FlashcardType = Literal["summary", "multiple-choice", "open-ended", "audio"]


class Option(BaseModel):
    text: str
    isCorrect: bool


class FlashcardContent(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    summary: Optional[str] = None
    answer: Optional[str] = None
    options: Optional[list[Option]] = None
    translation: Optional[str] = None
    # audioUrl pode ser uma data URI (ex.: "data:audio/mp3;base64,...."), nao
    # so um URL http(s) - o Laravel tambem so valida como string livre.
    audioUrl: Optional[str] = None


class SubmitFlashcardRequest(BaseModel):
    flashcard_id: int = Field(gt=0)
    categoria: str = Field(min_length=1, max_length=255)
    tipo: FlashcardType
    usuario: int = Field(gt=0)
    flashcard: FlashcardContent


class UpdateFlashcardRequest(BaseModel):
    categoria: str = Field(min_length=1, max_length=255)
    tipo: FlashcardType
    usuario: int = Field(gt=0)
    flashcard: FlashcardContent


class DeleteFlashcardRequest(BaseModel):
    usuario: int = Field(gt=0)


class IndexQueryParams(BaseModel):
    user_id: int = Field(gt=0)
    page: int = Field(default=1, ge=1)
    per_page: Optional[int] = Field(default=None, ge=1)
