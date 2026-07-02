import os
import subprocess
from pathlib import Path

os.environ["DB_NAME"] = "tesouraria_test"

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.database import get_connection, release_connection, release_connection
from app.main import app
from scripts.migrar import aplicar_migracoes


def _psql(*args):
    ambiente = {**os.environ, "PGPASSWORD": settings.DB_PASSWORD}
    subprocess.run(
        ["psql", "-h", settings.DB_HOST, "-p", settings.DB_PORT, "-U", settings.DB_USER, *args],
        check=True, env=ambiente, capture_output=True, text=True,
    )


# ─── fixtures ─────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session", autouse=True)
def recriar_estrutura_bd_teste():
    """Corre uma vez por sessão: apaga o schema e reconstrói-o aplicando
    todas as migrações em scripts/migrations/, pela mesma ordem que usarias
    em produção. Para alterar a BD, cria sempre um novo ficheiro de migração
    — nunca edites um já aplicado."""
    assert settings.DB_NAME == "tesouraria_test", "Isto só pode correr contra a BD de teste!"
    _psql("-d", settings.DB_NAME, "-c", "DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    aplicar_migracoes()


@pytest.fixture(autouse=True)
def limpar_bd():
    assert os.getenv("DB_NAME") == "tesouraria_test", "Os testes só podem correr contra a BD de teste!"
    app.state.limiter.reset()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        TRUNCATE utilizadores, contas, categorias, categorias_aprendidas,
                 movimentos, ajustes_saldo RESTART IDENTITY CASCADE
    """)
    conn.commit()
    cursor.close()
    release_connection(conn)
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def headers_autenticado(client):
    r = client.post("/registro", json={
        "nome": "Ana", "email": "ana@exemplo.com", "password": "senha123"
    })
    token = r.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def conta_id(client, headers_autenticado):
    client.post("/contas", json={
        "nome": "Conta Principal", "banco": "CGD", "tipo": "Conta Corrente",
        "iban": "PT50000000000000000000000", "moeda": "EUR", "saldo": 1000.0,
    }, headers=headers_autenticado)
    return client.get("/contas", headers=headers_autenticado).json()[0]["id"]


@pytest.fixture
def categoria_id(client, headers_autenticado):
    categorias = client.get("/categorias", headers=headers_autenticado).json()
    return next(c["id"] for c in categorias if not c["eh_recebimento"])


# gerar novo schema.sql semper que altero base de dados de desenvolvimento
# pg_dump --schema-only --no-owner -d tesouraria > scripts/schema.sql

# correr testes
# python -m pytest tests/ -v