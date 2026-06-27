from tests.helpers import hoje, dias_atras


def movimento_exemplo(conta_id, categoria_id, **overrides):
    base = {
        "conta_id": conta_id, "data": hoje(), "descricao": "Compra teste",
        "valor": -50.0, "categoria_id": categoria_id,
    }
    base.update(overrides)
    return base


def test_listar_movimentos(client, headers_autenticado, conta_id, categoria_id):
    client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id), headers=headers_autenticado)
    r = client.get("/movimentos", headers=headers_autenticado)
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["descricao"] == "Compra teste"


def test_filtrar_movimentos_por_conta(client, headers_autenticado, conta_id, categoria_id):
    client.post("/contas", json={
        "nome": "Outra Conta", "banco": "BPI", "tipo": "corrente",
        "iban": "PT50111111111111111111111", "moeda": "EUR", "saldo": 500.0,
    }, headers=headers_autenticado)
    outra_conta_id = [c for c in client.get("/contas", headers=headers_autenticado).json() if c["nome"] == "Outra Conta"][0]["id"]

    client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id, descricao="Da Principal"), headers=headers_autenticado)
    client.post("/movimentos", json=movimento_exemplo(outra_conta_id, categoria_id, descricao="Da Outra"), headers=headers_autenticado)

    r = client.get(f"/movimentos?conta_id={conta_id}", headers=headers_autenticado)
    movimentos = r.json()
    assert len(movimentos) == 1
    assert movimentos[0]["descricao"] == "Da Principal"


def test_filtrar_movimentos_por_direcao(client, headers_autenticado, conta_id, categoria_id):
    categorias = client.get("/categorias", headers=headers_autenticado).json()
    categoria_entrada_id = [c for c in categorias if c["eh_recebimento"]][0]["id"]

    client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id, descricao="Saída"), headers=headers_autenticado)
    client.post("/movimentos", json=movimento_exemplo(
        conta_id, categoria_entrada_id, descricao="Entrada", valor=200.0
    ), headers=headers_autenticado)

    r_in = client.get("/movimentos?direcao=in", headers=headers_autenticado)
    assert len(r_in.json()) == 1
    assert r_in.json()[0]["descricao"] == "Entrada"

    r_out = client.get("/movimentos?direcao=out", headers=headers_autenticado)
    assert len(r_out.json()) == 1
    assert r_out.json()[0]["descricao"] == "Saída"


def test_filtrar_movimentos_por_periodo(client, headers_autenticado, conta_id, categoria_id):
    ajustes = client.get(f"/contas/{conta_id}/ajustes-saldo", headers=headers_autenticado).json()
    client.put(f"/ajustes-saldo/{ajustes[0]['id']}", json={
        "data": dias_atras(60), "saldo_real": 1000.0,
    }, headers=headers_autenticado)

    client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id, data=hoje(), descricao="Hoje"), headers=headers_autenticado)
    client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id, data=dias_atras(45), descricao="Antigo"), headers=headers_autenticado)

    r = client.get(f"/movimentos?data_de={dias_atras(50)}&data_ate={dias_atras(20)}", headers=headers_autenticado)
    movimentos = r.json()
    assert len(movimentos) == 1
    assert movimentos[0]["descricao"] == "Antigo"


def test_editar_movimento(client, headers_autenticado, conta_id, categoria_id):
    client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id), headers=headers_autenticado)
    movimento_id = client.get("/movimentos", headers=headers_autenticado).json()[0]["id"]

    r = client.put(f"/movimentos/{movimento_id}", json=movimento_exemplo(
        conta_id, categoria_id, descricao="Descrição Editada", valor=-75.0
    ), headers=headers_autenticado)
    assert r.status_code == 200

    movimentos = client.get("/movimentos", headers=headers_autenticado).json()
    assert movimentos[0]["descricao"] == "Descrição Editada"
    assert movimentos[0]["valor"] == -75.0


def test_eliminar_movimento(client, headers_autenticado, conta_id, categoria_id):
    client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id), headers=headers_autenticado)
    movimento_id = client.get("/movimentos", headers=headers_autenticado).json()[0]["id"]

    r = client.delete(f"/movimentos/{movimento_id}", headers=headers_autenticado)
    assert r.status_code == 200
    assert client.get("/movimentos", headers=headers_autenticado).json() == []


def test_movimento_afeta_saldo_atual_da_conta(client, headers_autenticado, conta_id, categoria_id):
    client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id, valor=-300.0), headers=headers_autenticado)

    contas = client.get("/contas", headers=headers_autenticado).json()
    assert contas[0]["saldo"] == 700.0  # 1000 - 300


def test_movimentos_de_outro_utilizador_nao_aparecem(client, headers_autenticado, conta_id, categoria_id):
    client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id), headers=headers_autenticado)

    client.post("/registro", json={"nome": "Outro", "email": "outro@exemplo.com", "password": "senha123"})
    r_outro = client.post("/login", json={"email": "outro@exemplo.com", "password": "senha123"})
    headers_outro = {"Authorization": f"Bearer {r_outro.json()['token']}"}

    r = client.get("/movimentos", headers=headers_outro)
    assert r.json() == []


def test_criar_movimento_antes_da_reconciliacao_falha(client, headers_autenticado, conta_id, categoria_id):
    r = client.post("/movimentos", json=movimento_exemplo(
        conta_id, categoria_id, data=dias_atras(10)
    ), headers=headers_autenticado)
    assert r.status_code == 400


def test_editar_movimento_para_data_antes_da_reconciliacao_falha(client, headers_autenticado, conta_id, categoria_id):
    client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id), headers=headers_autenticado)
    movimento_id = client.get("/movimentos", headers=headers_autenticado).json()[0]["id"]

    r = client.put(f"/movimentos/{movimento_id}", json=movimento_exemplo(
        conta_id, categoria_id, data=dias_atras(10)
    ), headers=headers_autenticado)
    assert r.status_code == 400


def test_criar_movimento_com_categoria_da_direcao_errada_falha(client, headers_autenticado, conta_id):
    categorias = client.get("/categorias", headers=headers_autenticado).json()
    categoria_entrada = next(c for c in categorias if c["eh_recebimento"])

    r = client.post("/movimentos", json={
        "conta_id": conta_id, "data": hoje(), "descricao": "Errado",
        "valor": -50.0, "categoria_id": categoria_entrada["id"],
    }, headers=headers_autenticado)
    assert r.status_code == 400