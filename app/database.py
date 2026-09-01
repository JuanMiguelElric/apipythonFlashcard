from neo4j import Driver, GraphDatabase

_driver: Driver | None = None
_database: str = "neo4j"


def init_driver(app) -> None:
    global _driver, _database
    cfg = app.config
    _driver = GraphDatabase.driver(
        cfg["NEO4J_URI"],
        auth=(cfg["NEO4J_USERNAME"], cfg["NEO4J_PASSWORD"]),
        max_connection_lifetime=cfg["NEO4J_MAX_CONNECTION_LIFETIME"],
        max_connection_pool_size=cfg["NEO4J_MAX_CONNECTION_POOL_SIZE"],
        connection_timeout=cfg["NEO4J_CONNECTION_TIMEOUT"],
    )
    _driver.verify_connectivity()
    _database = cfg["NEO4J_DATABASE"]

    from app.repositories.constraints import apply_constraints
    from app.repositories.migrations import migrate_relationship_names

    apply_constraints(_driver, _database)
    migrate_relationship_names(_driver, _database)


def get_driver() -> Driver:
    if _driver is None:
        raise RuntimeError("Driver Neo4j nao inicializado. Chame init_driver(app) no startup.")
    return _driver


def get_database() -> str:
    return _database


def close_driver() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None
