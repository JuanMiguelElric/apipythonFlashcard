from neo4j import Driver

# Neo4j nao permite renomear um tipo de relacionamento in-place - e preciso
# recriar a relacao com o novo tipo e apagar a antiga. Nenhuma das relacoes
# deste modelo carrega propriedades, entao um CREATE+DELETE simples basta.
# Idempotente: roda a cada startup (app/database.py:init_driver), mas so
# encontra registros para migrar na primeira vez apos o deploy desta mudanca.
_RELATIONSHIP_RENAMES = [
    ("TIPO_do_flash_card", "TIPO_DO_FLASHCARD", "tipo", "flashcard"),
    ("Criado_por", "CRIADO_POR", "flashcard", "usuario"),
]


def migrate_relationship_names(driver: Driver, database: str = "neo4j") -> None:
    for old_type, new_type, from_label, to_label in _RELATIONSHIP_RENAMES:
        driver.execute_query(
            f"""
            MATCH (a:{from_label})-[r:{old_type}]->(b:{to_label})
            CREATE (a)-[:{new_type}]->(b)
            DELETE r
            """,
            database_=database,
        )
