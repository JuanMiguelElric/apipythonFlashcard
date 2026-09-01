import logging

from flask import Flask, jsonify

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 500
    code = "INTERNAL_ERROR"

    def __init__(self, message: str, details=None):
        super().__init__(message)
        self.message = message
        self.details = details

    def to_response(self):
        body = {"error": {"code": self.code, "message": self.message}}
        if self.details is not None:
            body["error"]["details"] = self.details
        return jsonify(body), self.status_code


class ValidationAppError(AppError):
    status_code = 400
    code = "VALIDATION_ERROR"


class UnauthorizedError(AppError):
    status_code = 401
    code = "UNAUTHORIZED"


class ForbiddenError(AppError):
    status_code = 403
    code = "FORBIDDEN"


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"


class ConflictError(AppError):
    status_code = 409
    code = "OWNERSHIP_CONFLICT"


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def _handle_app_error(err: AppError):
        return err.to_response()

    @app.errorhandler(404)
    def _handle_404(_err):
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Rota nao encontrada."}}), 404

    @app.errorhandler(405)
    def _handle_405(_err):
        return jsonify({"error": {"code": "METHOD_NOT_ALLOWED", "message": "Metodo nao permitido."}}), 405

    @app.errorhandler(Exception)
    def _handle_unexpected(err: Exception):
        # Detalhe completo (stacktrace, mensagem do driver Neo4j, etc.) so vai
        # para o log interno - o cliente nunca ve mais que uma mensagem generica.
        logger.exception("Erro nao tratado")
        return (
            jsonify({"error": {"code": "INTERNAL_ERROR", "message": "Nao foi possivel processar a solicitacao."}}),
            500,
        )
