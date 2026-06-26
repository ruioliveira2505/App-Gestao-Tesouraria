from conftest import hoje


def conta_exemplo(**overrides):
    base = {
        "nome": "Conta Principal", "banco": "CGD", "tipo": "corrente",
        "iban": "PT50000000000000000000000", "moeda": "EUR", "saldo": 1000.0,
    }
    base.update(overrides)
    return base


def test_criar_conta(client, headers_autenticado):
    r = client.post("/contas", json=conta_exemplo(), headers=headers_autenticado)
    assert r.status_code == 200


def test_listar_contas_reflete_saldo_inicial(client, headers_autenticado):
    client.post("/contas", json=conta_exemplo(), headers=headers_autenticado)
    r = client.get("/contas", headers=headers_autenticado)
    contas = r.json()
    assert len(contas) == 1
    assert contas[0]["saldo"] == 1000.0


def test_editar_conta(client, headers_autenticado):
    client.post("/contas", json=conta_exemplo(), headers=headers_autenticado)
    conta_id = client.get("/contas", headers=headers_autenticado).json()[0]["id"]

    r = client.put(f"/contas/{conta_id}", json={
        "nome": "Conta Renomeada", "banco": "CGD", "tipo": "corrente",
        "iban": "PT50000000000000000000000", "moeda": "EUR",
    }, headers=headers_autenticado)
    assert r.status_code == 200

    contas = client.get("/contas", headers=headers_autenticado).json()
    assert contas[0]["nome"] == "Conta Renomeada"


def test_eliminar_conta_sem_movimentos(client, headers_autenticado):
    client.post("/contas", json=conta_exemplo(), headers=headers_autenticado)
    conta_id = client.get("/contas", headers=headers_autenticado).json()[0]["id"]

    r = client.delete(f"/contas/{conta_id}", headers=headers_autenticado)
    assert r.status_code == 200
    assert client.get("/contas", headers=headers_autenticado).json() == []


def test_eliminar_conta_com_movimentos_pede_confirmacao(client, headers_autenticado):
    client.post("/contas", json=conta_exemplo(), headers=headers_autenticado)
    conta_id = client.get("/contas", headers=headers_autenticado).json()[0]["id"]
    categoria_id = client.get("/categorias", headers=headers_autenticado).json()[0]["id"]

    client.post("/movimentos", json={
        "conta_id": conta_id, "data": hoje(), "descricao": "Teste",
        "valor": -50.0, "categoria_id": categoria_id,
    }, headers=headers_autenticado)

    r = client.delete(f"/contas/{conta_id}", headers=headers_autenticado)
    assert r.status_code == 400  # sem ?forcar=true deve ser bloqueado


def test_eliminar_conta_com_forcar_remove_tudo(client, headers_autenticado):
    client.post("/contas", json=conta_exemplo(), headers=headers_autenticado)
    conta_id = client.get("/contas", headers=headers_autenticado).json()[0]["id"]
    categoria_id = client.get("/categorias", headers=headers_autenticado).json()[0]["id"]

    client.post("/movimentos", json={
        "conta_id": conta_id, "data": hoje(), "descricao": "Teste",
        "valor": -50.0, "categoria_id": categoria_id,
    }, headers=headers_autenticado)

    r = client.delete(f"/contas/{conta_id}?forcar=true", headers=headers_autenticado)
    assert r.status_code == 200
    assert client.get("/movimentos", headers=headers_autenticado).json() == []