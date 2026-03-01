class FlashcardRepository:
    @staticmethod
    def save(driver, categoria, tipo, flashcard, usuario):
        # Extrair os valores de flashcard
        titulo = flashcard.get('titulo', '')
        descricao = flashcard.get('descricao', '')

        driver.execute_query(
            """
            MERGE (c:categoria {categoria:$categoria})
            MERGE (t:tipo {tipo:$tipo})
            MERGE (f:flashcard {titulo:$titulo, descricao:$descricao})
            MERGE (u:usuario {usuario:$usuario})

            MERGE (c)-[:CATEGORIA]->(t)
            MERGE (t)-[:TIPO_do_flash_card]->(f)
            MERGE (f)-[:Criado_por]->(u)
            """,
            categoria=categoria,
            tipo=tipo,
            titulo=titulo,
            descricao=descricao,
            usuario=usuario
        )