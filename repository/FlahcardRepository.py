class FlashcardRepository:
    def index(driver):
        # Executa a consulta Cypher
        result = driver.execute_query(
            """
            MATCH (c:categoria)-[r1:CATEGORIA]->(t:tipo)-[r2:TIPO_do_flash_card]->(f:flashcard)-[r3:Criado_por]->(u:usuario)
            RETURN c, t, f, u, r1, r2, r3
            """
        )


        # Inicializa a lista para armazenar os dados dos flashcards
        flashcards_json = []

        # Processa os registros retornados
        for record in result.records:
            # Dicionário para armazenar os dados do registro
            row = {}

            # Itera sobre os itens do registro (chave-valor)
            for key, value in record.items():
                if hasattr(value, "properties"):
                    # Se for um nó ou relacionamento, acessa as propriedades
                    row[key] = value.properties
                else:
                    # Se não for um nó ou relacionamento, armazena o valor diretamente
                    row[key] = value

            # Agora que temos as propriedades, vamos extrair os dados relevantes
            categoria = row['c'].get('categoria', '')
            tipo = row['t'].get('tipo', '')
            question = row['f'].get('titulo','')
            multiple_choice = row['f'].get('multiple_choice','')
            summary = row['f'].get('descricao','')
            usuario = row['u'].get('usuario', '')

            # Adiciona os dados no formato JSON

            flashcards_json.append({
                'usuario': usuario,
                'categoria': categoria,
                'tipo':  tipo,
                'flashcard':{
                    'question':question,
                    'summary':summary,
                    'multiple-choice':multiple_choice
                }

            })

        return flashcards_json
    @staticmethod
    def save(driver, categoria, tipo, flashcard, usuario):
        try:
            # Extrair os valores de flashcard
            titulo = flashcard.get('question', '')
            descricao = flashcard.get('summary', None)
            open_ended = flashcard.get('open-ended', None)
            multiple_choice = flashcard.get('multiple-choice', None)

            # Garantir que valores nulos sejam substituídos por um valor válido
            if multiple_choice is None:
                multiple_choice = ''  # Ou outro valor padrão, como 'Não especificado' ou False
            
            if open_ended is None:
                open_ended = False  # Ou outro valor padrão, como False para questões de múltipla escolha
            
            # Executa a consulta Cypher
            driver.execute_query(
                """
                MERGE (c:categoria {categoria:$categoria})
                MERGE (t:tipo {tipo:$tipo})
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