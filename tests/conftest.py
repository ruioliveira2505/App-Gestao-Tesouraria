import os
import subprocess
from pathlib import Path

os.environ["DB_NAME"] = "tesouraria_test"

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.database import get_connection
from app.main import app


CAMINHO_SCHEMA = Path(__file__).resolve().parent.parent / "scripts" / "schema.sql"


def _psql(*args):
    ambiente = {**os.environ, "PGPASSWORD": settings.DB_PASSWORD}
    subprocess.run(
        ["psql", "-h", settings.DB_HOST, "-p", settings.DB_PORT, "-U", settings.DB_USER, *args],
        check=True, env=ambiente, capture_output=True, text=True,
    )


# ─── fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def recriar_estrutura_bd_teste():
    """Corre uma vez por sessão de pytest: apaga e recria a BD de testes a
    partir de scripts/schema.sql. Assim, qualquer ALTER TABLE/CREATE INDEX
    que apliques à BD de produção só precisa de ser refletido em schema.sql
    — a BD de testes sincroniza-se sozinha na próxima vez que correres pytest."""
    assert settings.DB_NAME == "tesouraria_test", "Isto só pode correr contra a BD de teste!"
    _psql("-d", settings.DB_NAME, "-c", "DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    _psql("-d", settings.DB_NAME, "-f", str(CAMINHO_SCHEMA))


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
    conn.close()
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
        "nome": "Conta Principal", "banco": "CGD", "tipo": "corrente",
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