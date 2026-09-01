import os


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Variavel de ambiente obrigatoria ausente: {name}")
    return value


class Config:
    NEO4J_URI = _require("NEO4J_URI")
    NEO4J_USERNAME = _require("NEO4J_USERNAME")
    NEO4J_PASSWORD = _require("NEO4J_PASSWORD")
    NEO4J_DATABASE = os.environ.get("NEO4J_DATABASE", "neo4j")
    NEO4J_MAX_CONNECTION_LIFETIME = int(os.environ.get("NEO4J_MAX_CONNECTION_LIFETIME", "3600"))
    NEO4J_MAX_CONNECTION_POOL_SIZE = int(os.environ.get("NEO4J_MAX_CONNECTION_POOL_SIZE", "50"))
    NEO4J_CONNECTION_TIMEOUT = int(os.environ.get("NEO4J_CONNECTION_TIMEOUT", "30"))

    SERVICE_TOKEN = _require("SERVICE_TOKEN")

    DEFAULT_PAGE_SIZE = int(os.environ.get("DEFAULT_PAGE_SIZE", "50"))
    MAX_PAGE_SIZE = int(os.environ.get("MAX_PAGE_SIZE", "200"))

    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
