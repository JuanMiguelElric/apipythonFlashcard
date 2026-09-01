import hmac

from flask import current_app, request

from app.errors import UnauthorizedError


def require_service_token() -> None:
    token = request.headers.get("X-Service-Token", "")
    expected = current_app.config["SERVICE_TOKEN"]

    if not token or not hmac.compare_digest(token, expected):
        raise UnauthorizedError("Token de servico ausente ou invalido.")
