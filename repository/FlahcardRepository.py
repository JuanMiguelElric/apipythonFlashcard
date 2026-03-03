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
            titulo = row['f'].get('titulo', '')
            descricao = row['f'].get('descricao', '')
            usuario = row['u'].get('usuario', '')

            # Criadores dos relacionamentos
            criador_categoria = row['r1'].get('criador', None)
            criador_tipo = row['r2'].get('criador', None)
            criador_flashcard = row['r3'].get('criador', None)

            # Adiciona os dados no formato JSON
            flashcards_json.append({
                'usuario': usuario,
                'categoria': {
                    'nome': categoria,
                    'criador': criador_categoria
                },
                'tipo': {
                    'nome': tipo,
                    'criador': criador_tipo
                },
                'flashcard': {
                    'titulo': titulo,
                    'descricao': descricao,
                    'criador': criador_flashcard
                },

            })

        return flashcards_json
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