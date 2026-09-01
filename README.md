# Flashcard Service (Python + Neo4j)

Microsserviço interno usado pelo backend Laravel do FlashMind para armazenar e
consultar o conteúdo e as relações dos flashcards. Não é a API pública do
sistema.

```text
React → Laravel + MySQL → Python + Neo4j (este serviço)
```

Laravel/MySQL é a fonte de verdade para autenticação de usuário final e para
o `flashcard_id` (id estável, originado em `flashcard_items.id` no MySQL).
Este serviço nunca identifica um flashcard pelo título — apenas por
`flashcard_id` — e nunca autentica o usuário final: ele confia no Laravel
para isso e apenas valida que a chamada HTTP vem do próprio Laravel
(autenticação serviço-a-serviço) e que o `usuario` informado é o dono do
recurso (ownership).

## Instalação

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows
pip install -r requirements.txt
cp .env.example .env           # preencher com valores reais
python run.py
```

## Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `NEO4J_URI` | sim | ex.: `neo4j://127.0.0.1:7687` |
| `NEO4J_USERNAME` | sim | usuário do Neo4j |
| `NEO4J_PASSWORD` | sim | senha do Neo4j (nunca hardcoded no código) |
| `NEO4J_DATABASE` | não (default `neo4j`) | banco Neo4j a usar, se houver mais de um |
| `NEO4J_MAX_CONNECTION_LIFETIME` | não (default `3600`) | segundos |
| `NEO4J_MAX_CONNECTION_POOL_SIZE` | não (default `50`) | tamanho do pool |
| `NEO4J_CONNECTION_TIMEOUT` | não (default `30`) | segundos |
| `SERVICE_TOKEN` | sim | token compartilhado com o Laravel (ver Autenticação) |
| `DEFAULT_PAGE_SIZE` | não (default `50`) | tamanho de página quando `per_page` não é enviado |
| `MAX_PAGE_SIZE` | não (default `200`) | teto absoluto de itens por página |
| `FLASK_DEBUG` | não (default `false`) | nunca `true` em produção |
| `HOST` / `PORT` | não | `127.0.0.1` / `5000` |
| `LOG_LEVEL` | não (default `INFO`) | nível de log |

## Autenticação serviço-a-serviço

Todas as rotas em `/submit_flash`, `/flashcard/*` exigem o header:

```http
X-Service-Token: <valor de SERVICE_TOKEN>
```

Sem o header ou com valor incorreto: `401 UNAUTHORIZED`. A comparação usa
`hmac.compare_digest` (constant-time). `/health` não exige autenticação.

O valor de `SERVICE_TOKEN` deve ser idêntico ao configurado no lado Laravel
(`config/services.php -> flashcard_service.token` / `.env
FLASHCARD_SERVICE_TOKEN`).

## Endpoints

| Método | Rota | Auth | Finalidade |
|---|---|---|---|
| `POST` | `/submit_flash` | sim | cria um flashcard (ou re-envia pelo próprio dono) |
| `GET` | `/flashcard/index?user_id=&page=&per_page=` | sim | lista flashcards de um usuário, paginado |
| `PUT` | `/flashcard/<flashcard_id>` | sim | atualiza um flashcard existente (parcial) |
| `DELETE` | `/flashcard/<flashcard_id>` | sim | remove um flashcard (exige `usuario` no corpo) |
| `GET` | `/health` | não | `Neo4j` acessível? |

### POST /submit_flash

```json
{
  "flashcard_id": 123,
  "categoria": "ingles",
  "tipo": "summary",
  "usuario": 5,
  "flashcard": {
    "question": "Capital do Brasil",
    "summary": "Brasília",
    "answer": null,
    "options": null,
    "translation": null,
    "audioUrl": null
  }
}
```

`tipo` aceita `summary`, `multiple-choice`, `open-ended`, `audio` (valores
fixados pelo `StoreFlashcardRequest::rules()` do Laravel). `options`, quando
presente, é `[{"text": str, "isCorrect": bool}, ...]`. `audioUrl` pode ser
uma data URI (`data:audio/mp3;base64,...`), não apenas um URL http(s).

Resposta `201`: mesmo formato, com o estado **real** persistido (não um eco
do payload).

Se `flashcard_id` já existir e pertencer a outro usuário: `409
OWNERSHIP_CONFLICT`.

### PUT /flashcard/<flashcard_id> — update parcial

O corpo é igual ao de `POST /submit_flash` (sem `flashcard_id`, que vem da
URL). **Campos omitidos dentro de `flashcard` preservam o valor já
armazenado** — só os campos efetivamente enviados no JSON são sobrescritos.
Exemplo: enviar apenas `{"flashcard": {"question": "Nova pergunta"}}` atualiza
somente `question`; `summary`, `answer`, `options`, `translation` e
`audioUrl` continuam com o valor anterior. A resposta reflete o estado real
pós-update (não o payload enviado), então ela mostra os valores preservados.

`404 NOT_FOUND` se o `flashcard_id` não existir. `403 FORBIDDEN` se pertencer
a outro `usuario` (mesmo código usado pelo `DELETE` para o mesmo tipo de
violação — `409 OWNERSHIP_CONFLICT` fica reservado para o `POST
/submit_flash`, onde o conflito é descobrir, na hora de criar, que o
`flashcard_id` já existe sob outro dono).

### DELETE /flashcard/<flashcard_id>

```json
{ "usuario": 5 }
```

`204` em sucesso. `404 NOT_FOUND` se não existir. `403 FORBIDDEN` se
`usuario` não for o dono.

### GET /flashcard/index

Filtra exclusivamente no Cypher (nunca varre o grafo inteiro em memória).

```http
GET /flashcard/index?user_id=5&page=1&per_page=20
```

`user_id` obrigatório. `page` (default 1) e `per_page` (default
`DEFAULT_PAGE_SIZE`, teto `MAX_PAGE_SIZE`) opcionais. Resposta: lista de
grupos por `categoria`/`tipo`, cada um com sua lista de `flashcards`.

### Erros

Nunca é devolvido detalhe interno (stacktrace, mensagem do driver Neo4j,
Cypher, credenciais). Formato uniforme:

```json
{ "error": { "code": "VALIDATION_ERROR", "message": "Payload invalido.", "details": [...] } }
```

Códigos: `VALIDATION_ERROR` (400), `UNAUTHORIZED` (401), `FORBIDDEN` (403),
`NOT_FOUND` (404), `OWNERSHIP_CONFLICT` (409), `INTERNAL_ERROR` (500, sempre
genérico — detalhe completo só vai para o log).

## Modelo Neo4j

```text
(:categoria {categoria})
      │ CATEGORIA
      ▼
(:tipo {tipo, categoria})
      │ TIPO_DO_FLASHCARD
      ▼
(:flashcard {flashcard_id, titulo, descricao, answer, multiple_choice, translation, audio_url})
      │ CRIADO_POR
      ▼
(:usuario {user_id})
```

Nomenclatura de relacionamentos padronizada (`CATEGORIA`, `TIPO_DO_FLASHCARD`,
`CRIADO_POR`). Uma migração idempotente (`app/repositories/migrations.py`)
roda automaticamente no startup e converte qualquer relacionamento legado
(`TIPO_do_flash_card`, `Criado_por`) para o nome padronizado, sem apagar
nenhum node.

### Constraints (aplicadas automaticamente no startup, idempotentes)

```text
categoria_unique          FOR (c:categoria) REQUIRE c.categoria IS UNIQUE
tipo_unique                FOR (t:tipo) REQUIRE (t.tipo, t.categoria) IS UNIQUE
flashcard_id_unique        FOR (f:flashcard) REQUIRE f.flashcard_id IS UNIQUE
usuario_user_id_unique     FOR (u:usuario) REQUIRE u.user_id IS UNIQUE
usuario_unique (legado)    FOR (u:usuario) REQUIRE u.usuario IS UNIQUE
```

Não existe (e não deve ser recriada) uma constraint de unicidade sobre
`flashcard.titulo` — o título nunca é identidade; dois usuários podem ter
flashcards com o mesmo título como nodes distintos.

### Dados legados

Havia, antes desta reescrita, 103 nodes `:flashcard` sem `flashcard_id`
(criados quando o título ainda era a identidade). Eles foram deliberadamente
preservados e não migrados — não têm um `flashcard_id` de origem no MySQL
para receber, então ficam invisíveis para os endpoints novos (que sempre
filtram por `flashcard_id`/`user_id`), mas não foram apagados.

## Testes

```bash
pytest tests/ -v
```

Requer um Neo4j real acessível via `NEO4J_URI`/`NEO4J_USERNAME`/
`NEO4J_PASSWORD` (não há mock do banco — os testes de repository e de API
rodam contra Cypher de verdade). Os testes usam um namespace isolado
(`flashcard_id >= 900_000_000`, `categoria` prefixada com `__test__`) que é
limpo antes e depois de cada teste, sem tocar em dados reais.

Cobertura: autenticação, CRUD completo, ownership (update e delete por
usuário não-dono), update parcial preservando campos não enviados,
paginação, colisão de título entre usuários diferentes, formato de erro sem
vazamento de detalhes internos, idempotência do upsert, nomenclatura padronizada
de relacionamentos.
