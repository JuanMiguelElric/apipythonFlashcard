class FlashcardRepository:
    def index(driver):
        result = driver.execute_query("""
            MATCH (c:categoria)-[:CATEGORIA]->(t:tipo)-[:TIPO_do_flash_card]->(f:flashcard)-[:Criado_por]->(u:usuario)
            RETURN 
                c.categoria AS categoria,
                t.tipo AS tipo,
                u.usuario AS usuario,
                collect({
                    question: f.titulo,
                    summary: f.descricao,
                    multiple_choice: f.multiple_choice
                }) AS flashcards
        """)

        flashcards_json = []

        for record in result.records:
            flashcards_json.append({
                "categoria": record["categoria"],
                "tipo": record["tipo"],
                "usuario": record["usuario"],
                "flashcards": record["flashcards"]
            })

        return flashcards_json
    @staticmethod
    def save(driver, categoria, tipo, flashcard, usuario):
        print(flashcard)
        try:
            # Extrair os valores de flashcard
            titulo = flashcard.get('question', '')
            descricao = flashcard.get('summary', None)
            open_ended = flashcard.get('answer', None)
            multiple_choice = flashcard.get('multiple-choice', None)

            # Garantir que valores nulos sejam substituídos por um valor válido
            if multiple_choice is None:
                multiple_choice = ''  # Ou outro valor padrão, como 'Não especificado' ou False
            
            if open_ended is None:
                open_ended = False  # Ou outro valor padrão, como False para questões de múltipla escolha
            print(categoria) 
            # Executa a consulta Cypher
            driver.execute_query(
                """
                MERGE (c:categoria {categoria:$categoria})
                MERGE (t:tipo {tipo:$tipo, categoria:$categoria})
                MERGE (f:flashcard {titulo:$titulo, descricao:coalesce($descricao, ''), open_ended:coalesce($open_ended, false), multiple_choice:coalesce($multiple_choice, '')})
                MERGE (u:usuario {usuario:$usuario})

                MERGE (c)-[:CATEGORIA]->(t)
                MERGE (t)-[:TIPO_do_flash_card]->(f)
                MERGE (f)-[:Criado_por]->(u)
                """,
                categoria=categoria,
                tipo=tipo,
                titulo=titulo,
                descricao=descricao,
                open_ended=open_ended,
                multiple_choice=multiple_choice,
                usuario=usuario
            )
        except Exception as e:
            print(f"Erro ao salvar o flashcard: {e}")
            raise  # Relevanta a exceção para retornar o erro 500