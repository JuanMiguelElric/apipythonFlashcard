from neo4j import Driver

# Substitui o antigo arquivo solto "constraints" (nunca executado por
# codigo - SHOW CONSTRAINTS no banco em uso confirmou que nenhuma delas
# jamais foi aplicada). Aplicadas de forma idempotente no startup da app
# (app/database.py:init_driver), nunca dependendo de execucao manual.
#
# A antiga "flashcard_unique FOR (f:flashcard) REQUIRE f.titulo IS UNIQUE"
# foi deliberadamente REMOVIDA e nao deve ser recriada: ela impedia que
# dois flashcards de usuarios/categorias diferentes tivessem o mesmo texto
# de titulo, colidindo no mesmo node. A identidade do flashcard agora e
# flashcard_id (fornecido pelo Laravel/MySQL via flashcard_items.id).
CONSTRAINTS = [
    "CREATE CONSTRAINT categoria_unique IF NOT EXISTS "
    "FOR (c:categoria) REQUIRE c.categoria IS UNIQUE",
    "CREATE CONSTRAINT tipo_unique IF NOT EXISTS "
    "FOR (t:tipo) REQUIRE (t.tipo, t.categoria) IS UNIQUE",
    "CREATE CONSTRAINT flashcard_id_unique IF NOT EXISTS "
    "FOR (f:flashcard) REQUIRE f.flashcard_id IS UNIQUE",
    # Mantida por compatibilidade com os nodes legados (usuario=5, dado
    # de producao criado antes do flashcard_id existir) - nao e usada por
    # nenhum caminho de codigo novo.
    "CREATE CONSTRAINT usuario_unique IF NOT EXISTS "
    "FOR (u:usuario) REQUIRE u.usuario IS UNIQUE",
    "CREATE CONSTRAINT usuario_user_id_unique IF NOT EXISTS "
    "FOR (u:usuario) REQUIRE u.user_id IS UNIQUE",
]


def apply_constraints(driver: Driver, database: str = "neo4j") -> None:
    for statement in CONSTRAINTS:
        driver.execute_query(statement, database_=database)
