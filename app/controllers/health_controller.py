import logging

from flask import jsonify

from app.database import get_driver

logger = logging.getLogger(__name__)


def health():
    try:
        get_driver().verify_connectivity()
    except Exception:
        logger.exception("Health check: Neo4j inacessivel")
        return jsonify({"status": "degraded", "neo4j": "down"}), 503

    return jsonify({"status": "ok", "neo4j": "up"}), 200
