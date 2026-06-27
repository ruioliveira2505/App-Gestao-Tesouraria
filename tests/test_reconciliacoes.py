from tests.helpers import hoje, dias_atras

def test_conta_nasce_com_uma_reconciliacao(client, headers_autenticado, conta_id):
    r = client.get(f"/contas/{conta_id}/ajustes-saldo", headers=headers_autenticado)
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["saldo_real"] == 1000.0


def test_criar_reconciliacao_mais_antiga_nao_afeta_saldo_atual(client, headers_autenticado, conta_id):
    # a reconciliação de hoje é sempre a mais recente possível (não há datas futuras) —
    # por isso uma nova reconciliação no passado nunca a substitui
    r = client.post(f"/contas/{conta_id}/ajustes-saldo", json={
        "data": dias_atras(10), "saldo_real": 1500.0,
    }, headers=headers_autenticado)
    assert r.status_code == 200

    contas = client.get("/contas", headers=headers_autenticado).json()
    assert contas[0]["saldo"] == 1000.0


def test_editar_reconciliacao_de_hoje_atualiza_saldo_atual(client, headers_autenticado, conta_id):
    # a forma correta de corrigir o saldo "a partir de agora" é editar a reconciliação de hoje
    ajustes = client.get(f"/contas/{conta_id}/ajustes-saldo", headers=headers_autenticado).json()
    ajuste_id = ajustes[0]["id"]

    r = client.put(f"/ajustes-saldo/{ajuste_id}", json={
        "data": hoje(), "saldo_real": 1500.0,
    }, headers=headers_autenticado)
    assert r.status_code == 200

    contas = client.get("/contas", headers=headers_autenticado).json()
    assert contas[0]["saldo"] == 1500.0


def test_criar_reconciliacao_data_futura_falha(client, headers_autenticado, conta_id):
    r = client.post(f"/contas/{conta_id}/ajustes-saldo", json={
        "data": "2099-01-01", "saldo_real": 1500.0,
    }, headers=headers_autenticado)
    assert r.status_code == 400


def test_criar_reconciliacao_data_duplicada_falha(client, headers_autenticado, conta_id):
    client.post(f"/contas/{conta_id}/ajustes-saldo", json={
        "data": dias_atras(5), "saldo_real": 1500.0,
    }, headers=headers_autenticado)
    r = client.post(f"/contas/{conta_id}/ajustes-saldo", json={
        "data": dias_atras(5), "saldo_real": 2000.0,
    }, headers=headers_autenticado)
    assert r.status_code == 400


def test_eliminar_unica_reconciliacao_falha(client, headers_autenticado, conta_id):
    ajustes = client.get(f"/contas/{conta_id}/ajustes-saldo", headers=headers_autenticado).json()
    ajuste_id = ajustes[0]["id"]

    r = client.delete(f"/ajustes-saldo/{ajuste_id}", headers=headers_autenticado)
    assert r.status_code == 400


def test_eliminar_reconciliacao_com_outra_restante_funciona(client, headers_autenticado, conta_id):
    client.post(f"/contas/{conta_id}/ajustes-saldo", json={
        "data": dias_atras(10), "saldo_real": 1500.0,
    }, headers=headers_autenticado)

    ajustes = client.get(f"/contas/{conta_id}/ajustes-saldo", headers=headers_autenticado).json()
    ajuste_hoje_id = [a for a in ajustes if a["saldo_real"] == 1000.0][0]["id"]

    r = client.delete(f"/ajustes-saldo/{ajuste_hoje_id}", headers=headers_autenticado)
    assert r.status_code == 200


def test_editar_reconciliacao_data_futura_falha(client, headers_autenticado, conta_id):
    ajustes = client.get(f"/contas/{conta_id}/ajustes-saldo", headers=headers_autenticado).json()
    ajuste_id = ajustes[0]["id"]

    r = client.put(f"/ajustes-saldo/{ajuste_id}", json={
        "data": "2099-01-01", "saldo_real": 1500.0,
    }, headers=headers_autenticado)
    assert r.status_code == 400


def test_eliminar_reconciliacao_intermedia_recalcula_saldo_corretamente(
    client, headers_autenticado, conta_id, categoria_id
):
    # move a reconciliação inicial (hoje, 1000€) para um ponto A no passado
    ajustes = client.get(f"/contas/{conta_id}/ajustes-saldo", headers=headers_autenticado).json()
    ajuste_a_id = ajustes[0]["id"]
    client.put(f"/ajustes-saldo/{ajuste_a_id}", json={
        "data": dias_atras(30), "saldo_real": 1000.0,
    }, headers=headers_autenticado)

    # movimento entre A e B
    client.post("/movimentos", json={
        "conta_id": conta_id, "data": dias_atras(20), "descricao": "Compra antiga",
        "valor": -100.0, "categoria_id": categoria_id,
    }, headers=headers_autenticado)

    # B: reconciliação intermédia, mais recente que A
    client.post(f"/contas/{conta_id}/ajustes-saldo", json={
        "data": dias_atras(10), "saldo_real": 2000.0,
    }, headers=headers_autenticado)

    # movimento depois de B
    client.post("/movimentos", json={
        "conta_id": conta_id, "data": dias_atras(5), "descricao": "Compra recente",
        "valor": -200.0, "categoria_id": categoria_id,
    }, headers=headers_autenticado)

    contas = client.get("/contas", headers=headers_autenticado).json()
    assert contas[0]["saldo"] == 1800.0  # 2000 - 200; o movimento entre A e B já não conta

    # eliminar B — só resta A; agora TODOS os movimentos desde A contam
    ajustes = client.get(f"/contas/{conta_id}/ajustes-saldo", headers=headers_autenticado).json()
    ajuste_b_id = [a for a in ajustes if a["saldo_real"] == 2000.0][0]["id"]
    r = client.delete(f"/ajustes-saldo/{ajuste_b_id}", headers=headers_autenticado)
    assert r.status_code == 200

    contas = client.get("/contas", headers=headers_autenticado).json()
    assert contas[0]["saldo"] == 700.0  # 1000 - 100 - 200, sem o ponto B


def test_reconciliacao_mais_antiga_nao_pode_ficar_depois_do_primeiro_movimento(
    client, headers_autenticado, conta_id, categoria_id
):
    ajustes = client.get(f"/contas/{conta_id}/ajustes-saldo", headers=headers_autenticado).json()
    ajuste_id = ajustes[0]["id"]
    client.put(f"/ajustes-saldo/{ajuste_id}", json={
        "data": dias_atras(30), "saldo_real": 1000.0,
    }, headers=headers_autenticado)

    client.post("/movimentos", json={
        "conta_id": conta_id, "data": dias_atras(30), "descricao": "Compra antiga",
        "valor": -100.0, "categoria_id": categoria_id,
    }, headers=headers_autenticado)

    r = client.put(f"/ajustes-saldo/{ajuste_id}", json={
        "data": dias_atras(15), "saldo_real": 1000.0,
    }, headers=headers_autenticado)
    assert r.status_code == 400


def test_criar_movimento_antes_da_reconciliacao_mais_antiga_falha(client, headers_autenticado, conta_id, categoria_id):
    r = client.post("/movimentos", json={
        "conta_id": conta_id, "data": dias_atras(10), "descricao": "Compra antiga",
        "valor": -50.0, "categoria_id": categoria_id,
    }, headers=headers_autenticado)
    assert r.status_code == 400


def test_criar_movimento_apos_recuar_reconciliacao_funciona(client, headers_autenticado, conta_id, categoria_id):
    ajustes = client.get(f"/contas/{conta_id}/ajustes-saldo", headers=headers_autenticado).json()
    ajuste_id = ajustes[0]["id"]
    client.put(f"/ajustes-saldo/{ajuste_id}", json={
        "data": dias_atras(30), "saldo_real": 1000.0,
    }, headers=headers_autenticado)

    r = client.post("/movimentos", json={
        "conta_id": conta_id, "data": dias_atras(10), "descricao": "Compra antiga",
        "valor": -50.0, "categoria_id": categoria_id,
    }, headers=headers_autenticado)
    assert r.status_code == 200