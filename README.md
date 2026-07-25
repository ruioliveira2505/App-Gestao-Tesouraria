# App Gestão de Tesouraria

App pessoal de gestão de finanças — backend em FastAPI + PostgreSQL (sem ORM), frontend em
HTML/CSS simples (`static/index.html`) com a lógica em módulos ES nativos, sem build nem
framework (`static/js/*.js`).

Para uma visão geral da estrutura do código (camadas, contrato de erros, conceitos de
domínio), ver [ARCHITECTURE.md](ARCHITECTURE.md).

## Arrancar em desenvolvimento

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/playwright install chromium   # só uma vez — o browser dos testes E2E
cp .env.example .env   # e preenche com valores reais
```

Cria as bases de dados (uma para desenvolvimento, uma para testes) e aplica as migrações:

```bash
createdb tesouraria
createdb tesouraria_test
.venv/bin/python -m scripts.migrar
```

Precisas de um servidor PostgreSQL a correr e do cliente `psql` disponível na linha de
comandos (os testes usam-no para recriar o schema de teste antes de cada corrida).

Corre o servidor:

```bash
.venv/bin/uvicorn app.main:app --reload
```

A app fica em `http://localhost:8000/static/index.html`.

## Testes

```bash
.venv/bin/python -m pytest tests/ -v
```

Os testes correm contra `tesouraria_test` (nunca contra a base de dados de
desenvolvimento) — o `conftest.py` recusa-se a correr se `DB_NAME` não for essa.

`tests/e2e/` tem testes de browser a sério (Playwright — arranca um servidor real e
controla um Chromium sem interface gráfica). São mais lentos que o resto da suite;
`pytest -m e2e` corre só esses, `pytest -m "not e2e"` salta-os.

Cobertura de código do backend:

```bash
.venv/bin/python -m pytest --cov=app --cov-report=term-missing
```

## Docker

```bash
cp .env.example .env   # e preenche pelo menos DB_PASSWORD e SECRET_KEY
docker compose up
```

Sobe a base de dados (Postgres 16) e a app, já com as migrações aplicadas. A app fica em
`http://localhost:8000/static/index.html`.
