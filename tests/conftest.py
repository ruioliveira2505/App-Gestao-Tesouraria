import os
os.environ["DB_NAME"] = "tesouraria_test"

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import get_connection


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
    r = client.post("/contas", json={
        "nome": "Conta Principal", "banco": "CGD", "tipo": "corrente",
        "iban": "PT50000000000000000000000", "moeda": "EUR", "saldo": 1000.0,
    }, headers=headers_autenticado)
    return client.get("/contas", headers=headers_autenticado).json()[0]["id"]


@pytest.fixture
def categoria_id(client, headers_autenticado):
    return client.get("/categorias", headers=headers_autenticado).json()[0]["id"]


# correr testes
# python -m pytest tests/ -v