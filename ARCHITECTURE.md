# Arquitectura

Visão geral de como o backend está organizado. O frontend (`static/index.html` +
`static/js/*.js`) fica fora do âmbito deste documento por agora — ver "Frontend — Código /
Arquitectura" em `analise-tesouraria.md` para a decisão de não usar framework nenhum
(módulos ES nativos, sem build).

## Camadas

```
app/routers/    HTTP: parsing do pedido, injecção de dependências, chama o serviço,
                devolve o response_model. Nenhuma regra de negócio nem SQL aqui.
app/services/   Regras de negócio + SQL directo (sem ORM — decisão registada em
                analise-tesouraria.md). Recebe sempre um cursor já aberto; nunca sabe
                o que é FastAPI/HTTP.
app/schemas/    Modelos Pydantic — um Input/Output por operação, não um genérico
                reutilizado em todo o lado.
app/core/       Infra-estrutura partilhada: configuração (pydantic-settings),
                autenticação/JWT, o contrato de erros, utilitários pequenos.
app/db/         Pool de ligações e a dependência `get_db`.
```

Um router típico:

```python
@router.post("/movimentos", response_model=OkResponse)
def criar_movimento(dados: MovimentoInput, utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db)):
    servico.criar_movimento(cursor, cursor.connection, utilizador["sub"], dados)
    return {"ok": True}
```

## Ligação à base de dados por pedido

`app/db/database.py::get_db` é uma dependência FastAPI que entrega um cursor
(`RealDictCursor` — acesso a colunas por nome, `row["coluna"]`) já dentro de uma
transacção: comita se o pedido terminar sem excepção, reverte e relança se não terminar.

O FastAPI só resolve cada dependência **uma vez por pedido** (é o comportamento por
omissão do `Depends`). Como `utilizador_atual` (a dependência de autenticação) também
depende de `get_db`, a verificação de sessão e o resto da rota acabam a partilhar a
mesma ligação — um pedido autenticado usa uma ligação à BD, não duas.

Serviços que precisam de comitar ou reverter a meio de uma operação (ex.
`criar_ajuste_saldo`, que reverte com `conn.rollback()` se apanhar uma reconciliação
duplicada, antes de continuar) recebem a ligação via `cursor.connection` — não há
nenhum sítio que abra uma ligação à parte.

## Erros

Toda a app devolve erros na mesma forma: `{"detail": {"code": "...", "message": "..."}}`.
`code` é estável (nunca muda de texto, para o cliente poder decidir com base nele);
`message` é só para mostrar.

- Nos **routers**: `erro_http(status_code, code, message)` (`app/core/errors.py`) —
  devolve um `HTTPException` normal.
- Nos **serviços**: `raise ErroDominio(status_code, code, message)`
  (`app/core/dominio.py`) — não depende do FastAPI de propósito, para um serviço poder
  ser chamado (e testado) sem um pedido HTTP a sério. Um exception handler global
  (`erro_dominio_handler`, registado em `app/main.py`) traduz para a mesma forma.
- Erros de validação do Pydantic (422) ganham o mesmo formato via
  `validation_exception_handler`, com um campo adicional `errors` (lista de todos os
  erros, não só o primeiro).

## Domínio — os conceitos que não são óbvios só a ler o código

- **Categorias**: árvore de dois níveis (grupo → categoria-folha) numa única tabela
  (`parent_id NULL` = grupo). Categorias `protegida=true` (ex. o fallback "Outros" de
  cada direcção) nunca podem ser editadas/eliminadas.
- **Contas e a âncora**: `contas.data_ancora`/`saldo_ancora` guardam o saldo antes de
  qualquer movimento — um atributo próprio da conta, não uma reconciliação. Fica sempre um
  dia antes da "Data de Início de Movimentos" (o que o utilizador vê/edita); edita-se via
  `GET`/`PUT /contas/{id}/inicio`, nunca através de `/ajustes-saldo`. `ajustes_saldo`
  guarda só reconciliações reais — ao contrário de uma versão anterior deste modelo, a
  âncora nunca foi (nem pode ser) uma linha dessa tabela, por isso não há necessidade de
  nenhum filtro a escondê-la. Para calcular "saldo numa data", `app/services/contas.py`
  define `PONTOS_SALDO_CTE`, que junta a âncora (de `contas`) com as reconciliações reais
  (de `ajustes_saldo`) numa só lista ordenável por data — reaproveitado por
  `listar_contas`/`saldo_em_data` e por `stats_saldo_diario` (`app/services/estatisticas.py`).
- **`origem_cat`** (`movimentos`): `manual` (utilizador escolheu/confirmou), `cache`
  (veio de `categorias_aprendidas` já confirmada), `llm` (sugestão automática, por
  confirmar) ou `sem_match` (fallback, por confirmar) — restrito por `CHECK` na BD.
  `llm`/`sem_match` é o que aparece como pendente em `/movimentos/pendentes/contagem`.
  A categorização automática (`app/services/categorizacao.py`, via API da Groq) só é
  chamada hoje por `scripts/seed_dev.py` — não há nenhum endpoint HTTP de importação de
  extractos ainda (ver `analise-tesouraria-historico.md`, secção "Higiene do repositório").
- **Tipos de id inconsistentes, e porquê fica assim**: `contas.id`/`movimentos.id` são
  `text` (UUID gerado em Python, `str(uuid.uuid4())`); `categorias`, `ajustes_saldo` e
  `utilizadores` usam `integer`/serial. Não foi decidido de propósito ("calhou", confirmado
  com o utilizador) — mas decidiu-se manter assim: migrar para `integer` só por
  uniformidade seria uma alteração grande (chave primária de duas tabelas + todas as
  foreign keys que apontam para elas) para corrigir algo cosmético, não um problema real.
  De propósito ou não, tem vantagens genuínas: o id é gerado antes do `INSERT` (sem precisar
  de `RETURNING id`) e não é sequencial (não dá para adivinhar quantas contas/movimentos
  existem a partir de um id). Ver `analise-tesouraria.md`, secção "Ronda de revisão
  ficheiro-a-ficheiro", para o registo completo desta decisão.

## SQL nativo, sem ORM

Decisão explícita, registada em detalhe em `analise-tesouraria-historico.md` (secção
"Arquitectura") — proporção, não desconfiança na ferramenta: as dores concretas
(acesso a colunas por nome, migrações, tipos na resposta) já estão resolvidas por vias
mais baratas (`RealDictCursor`, `scripts/migrations/`, `response_model`), e as CTEs
recursivas de `app/services/estatisticas.py` continuariam em SQL puro de qualquer forma.

## Migrações

`scripts/migrations/NNNN_nome.sql`, aplicadas por ordem numérica via
`python -m scripts.migrar` (regista o que já correu em `schema_migracoes`, por número
de versão). **Antes de criar uma migração nova, confirma o próximo número livre pela
BD** (`SELECT MAX(versao) FROM schema_migracoes`), não só pela pasta — os dois podem
divergir se um ficheiro for renomeado ou substituído depois de aplicado (já aconteceu
uma vez nesta app; ver `analise-tesouraria-historico.md`, secção "Modelo de dados /
Migrações").
