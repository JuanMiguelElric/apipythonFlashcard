

class FlashcardRepository:
    @staticmethod
    def save (driver, categoria, tipo, flashcard, usuario):
        driver.execute_query(
            """
            MERGE (c:categoria{categoria:$categoria})
            MERGE (t:tipo {tipo:$tipo})
            MERGE (f:flashcard {flashcard:$flashcard})
            MERGE (u:usuario {usuario:$usuario})

            MERGE (c)-[:CATEGORIA]->(t)
            MERGE (t)-[:TIPO_do_flash_card]->(f)
            MERGE (f)-[:Criado_por]->(u)
            """,
            categoria=categoria,
            tipo=tipo,
            flashcard=flashcard,
            usuario=usuario
        )