import itertools
import os

import pytest
from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402
from app.database import get_driver  # noqa: E402

# Namespace reservado para dados de teste. Nunca colide com os dados reais
# preservados no Neo4j (103 flashcards legados sem flashcard_id, usuario
# real com user_id=5, categorias "ingles"/"fisica"/"neo4j"/"matematica"/
# "hacking") nem com IDs reais futuros do MySQL (que comecam em 1).
TEST_ID_FLOOR = 900_000_000
TEST_CATEGORIA_PREFIX = "__test__"

_id_counter = itertools.count(TEST_ID_FLOOR + 1)


@pytest.fixture(scope="session")
def app():
    return create_app()


@pytest.fixture(scope="session")
def driver(app):
    return get_driver()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers():
    return {"X-Service-Token": os.environ["SERVICE_TOKEN"]}


@pytest.fixture
def next_id():
    def _next():
        return next(_id_counter)

    return _next


def _wipe_test_namespace(driver):
    driver.execute_query(
        "MATCH (f:flashcard) WHERE f.flashcard_id >= $floor DETACH DELETE f",
        floor=TEST_ID_FLOOR,
    )
    driver.execute_query(
        "MATCH (u:usuario) WHERE u.user_id >= $floor DETACH DELETE u",
        floor=TEST_ID_FLOOR,
    )
    driver.execute_query(
        "MATCH (t:tipo) WHERE t.categoria STARTS WITH $prefix DETACH DELETE t",
        prefix=TEST_CATEGORIA_PREFIX,
    )
    driver.execute_query(
        "MATCH (c:categoria) WHERE c.categoria STARTS WITH $prefix DETACH DELETE c",
        prefix=TEST_CATEGORIA_PREFIX,
    )


@pytest.fixture(autouse=True)
def clean_test_namespace(driver):
    _wipe_test_namespace(driver)
    yield
    _wipe_test_namespace(driver)
