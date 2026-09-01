from flask import Blueprint

from app.auth import require_service_token
from app.controllers import flashcard_controller

flashcard_bp = Blueprint("flashcard", __name__)
flashcard_bp.before_request(require_service_token)

# Caminho preservado (Laravel ja chama POST /submit_flash em
# app/Services/FlashcardServiceClient.php) - so o payload/semantica mudou.
flashcard_bp.add_url_rule("/submit_flash", view_func=flashcard_controller.submit, methods=["POST"])

flashcard_bp.add_url_rule("/flashcard/index", view_func=flashcard_controller.index, methods=["GET"])
flashcard_bp.add_url_rule("/flashcard/<int:flashcard_id>", view_func=flashcard_controller.update, methods=["PUT"])
flashcard_bp.add_url_rule("/flashcard/<int:flashcard_id>", view_func=flashcard_controller.destroy, methods=["DELETE"])
