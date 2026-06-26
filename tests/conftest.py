import os
os.environ["DB_NAME"] = "tesouraria_test"

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.db.database import get_connection
from app.main import app


# ─── fixtures ─────────────────────────────────────────────────────────────────

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
    return client.get("/categorias", headers=headers_autenticado).json()[0]["id"]


# ─── helpers partilhados (funções normais, não fixtures) ──────────────────────

def hoje():
    return str(date.today())


def dias_atras(n):
    return str(date.today() - timedelta(days=n))


def id_categoria(client, headers, nome_grupo, nome_categoria):
    arvore = client.get("/categorias/arvore", headers=headers).json()
    grupo = next(g for g in arvore if g["nome"] == nome_grupo)
    return next(c["id"] for c in grupo["categorias"] if c["nome"] == nome_categoria)


def criar_movimento(client, headers, conta_id, categoria_id, valor=-50.0, data=None, descricao="Teste"):
    r = client.post("/movimentos", json={
        "conta_id": conta_id, "data": data or hoje(), "descricao": descricao,
        "valor": valor, "categoria_id": categoria_id,
    }, headers=headers)
    assert r.status_code == 200, r.json()
    movimentos = client.get("/movimentos", headers=headers).json()
    return next(m for m in movimentos if m["descricao"] == descricao)["id"]


# correr testes
# python -m pytest tests/ -v