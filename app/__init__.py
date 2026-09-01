import atexit
import logging
import uuid

from dotenv import load_dotenv

load_dotenv()  # precisa rodar antes de importar app.config, que le os.environ no corpo da classe

from flask import Flask, g, request  # noqa: E402

from app.config import Config  # noqa: E402
from app.database import close_driver, init_driver  # noqa: E402
from app.errors import register_error_handlers  # noqa: E402
from app.logging_config import configure_logging  # noqa: E402
from app.routes import register_blueprints  # noqa: E402


def create_app(config: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config)

    configure_logging(app.config["LOG_LEVEL"])
    init_driver(app)
    register_error_handlers(app)
    register_blueprints(app)

    logger = logging.getLogger(__name__)

    @app.before_request
    def _assign_request_id():
        g.request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())

    @app.after_request
    def _echo_request_id(response):
        response.headers["X-Request-Id"] = getattr(g, "request_id", "")
        return response

    atexit.register(close_driver)
    logger.info("Flashcard service inicializado (debug=%s)", app.config["DEBUG"])

    return app
