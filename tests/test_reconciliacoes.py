from tests.helpers import dias_atras, hoje, recuar_ancora


def test_conta_nasce_apenas_com_a_ancora_sem_reconciliacoes_visiveis(client, headers_autenticado, conta_id):
    r = client.get(f"/contas/{conta_id}/ajustes-saldo", headers=headers_autenticado)
    assert r.status_code == 200
    assert r.json() == []


def test_inicio_da_conta_reflete_a_ancora_criada(client, headers_autenticado, conta_id):
    r = client.get(f"/contas/{conta_id}/inicio", headers=headers_autenticado)
    assert r.status_code == 200
    body = r.json()
    assert body["saldo_real"] == 1000.0
    assert body["data"] == hoje()  # âncora fica em dias_atras(1); início = âncora + 1 dia


def test_criar_reconciliacao_anterior_a_ancora_falha(client, headers_autenticado, conta_id):
    r = client.post(f"/contas/{conta_id}/ajustes-saldo", json={
        "data": dias_atras(10), "saldo_real": 1500.0,
    }, headers=headers_autenticado)
    assert r.status_code == 400


def test_editar_inicio_da_conta_atualiza_saldo_atual(client, headers_autenticado, conta_id):
    # a forma correta de corrigir o saldo "a partir de agora", numa conta que só tem a
    # âncora, é editar a própria Data de Início de Movimentos
    inicio = client.get(f"/contas/{conta_id}/inicio", headers=headers_autenticado).json()

    r = client.put(f"/contas/{conta_id}/inicio", json={
        "data": inicio["data"], "saldo_real": 1500.0,
    }, headers=headers_autenticado)
    assert r.status_code == 200

    contas = client.get("/contas", headers=headers_autenticado).json()
    assert contas[0]["saldo"] == 1500.0


def test_criar_reconciliacao_data_futura_falha(client, headers_autenticado, conta_id):
    r = client.post(f"/contas/{conta_id}/ajustes-saldo", json={
        "data": "2099-01-01", "saldo_real": 1500.0,
    }, headers=headers_autenticado)
    assert r.status_code == 400


def test_editar_inicio_com_data_futura_falha(client, headers_autenticado, conta_id):
    r = client.put(f"/contas/{conta_id}/inicio", json={
        "data": "2099-01-01", "saldo_real": 1500.0,
    }, headers=headers_autenticado)
    assert r.status_code == 400


def test_criar_reconciliacao_data_duplicada_falha(client, headers_autenticado, conta_id):
    recuar_ancora(client, headers_autenticado, conta_id, dias_atras(30))

    client.post(f"/contas/{conta_id}/ajustes-saldo", json={
        "data": dias_atras(10), "saldo_real": 1500.0,
    }, headers=headers_autenticado)
    r = client.post(f"/contas/{conta_id}/ajustes-saldo", json={
        "data": dias_atras(10), "saldo_real": 2000.0,
    }, headers=headers_autenticado)
    assert r.status_code == 400


# Nota: existia aqui um teste "não é possível eliminar a âncora" que ia buscar o id da
# âncora directamente à BD (ela não aparecia em GET /ajustes-saldo nem em GET /inicio) e
# confirmava que DELETE /ajustes-saldo/{id} rejeitava com 400 (EH_A_ANCORA). Desde que a
# âncora passou a ser um atributo de `contas` (data_ancora/saldo_ancora), em vez de uma
# linha "escondida" em `ajustes_saldo`, esse cenário deixou de ser possível de todo — não
# há nenhum id de `ajustes_saldo` que alguma vez seja a âncora, por isso o teste ficou sem
# objecto (o código EH_A_ANCORA foi removido de services/contas.py). Não substituído por
# outro: "a âncora nunca aparece no que /ajustes-saldo devolve" já fica coberto por
# test_conta_nasce_apenas_com_a_ancora_sem_reconciliacoes_visiveis.


def test_eliminar_reconciliacao_com_outra_restante_funciona(client, headers_autenticado, conta_id):
    recuar_ancora(client, headers_autenticado, conta_id, dias_atras(30))
    client.post(f"/contas/{conta_id}/ajustes-saldo", json={
        "data": dias_atras(20), "saldo_real": 1200.0,
    }, headers=headers_autenticado)
    client.post(f"/contas/{conta_id}/ajustes-saldo", json={
        "data": dias_atras(10), "saldo_real": 1500.0,
    }, headers=headers_autenticado)

    ajustes = client.get(f"/contas/{conta_id}/ajustes-saldo", headers=headers_autenticado).json()
    assert len(ajustes) == 2
    mais_recente_id = max(ajustes, key=lambda a: a["data"])["id"]

    r = client.delete(f"/ajustes-saldo/{mais_recente_id}", headers=headers_autenticado)
    assert r.status_code == 200

    ajustes_restantes = client.get(f"/contas/{conta_id}/ajustes-saldo", headers=headers_autenticado).json()
    assert len(ajustes_restantes) == 1


def test_eliminar_reconciliacao_intermedia_recalcula_saldo_corretamente(
    client, headers_autenticado, conta_id, categoria_id
):
    # move a âncora (hoje, 1000€) para um ponto A no passado
    recuar_ancora(client, headers_autenticado, conta_id, dias_atras(30))

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

    # eliminar B — só resta A (a âncora); agora TODOS os movimentos desde A contam
    ajuste_b_id = client.get(f"/contas/{conta_id}/ajustes-saldo", headers=headers_autenticado).json()[0]["id"]
    r = client.delete(f"/ajustes-saldo/{ajuste_b_id}", headers=headers_autenticado)
    assert r.status_code == 200

    contas = client.get("/contas", headers=headers_autenticado).json()
    assert contas[0]["saldo"] == 700.0  # 1000 - 100 - 200, sem o ponto B


def test_ancora_nao_pode_ficar_depois_do_primeiro_movimento(client, headers_autenticado, conta_id, categoria_id):
    recuar_ancora(client, headers_autenticado, conta_id, dias_atras(30))

    client.post("/movimentos", json={
        "conta_id": conta_id, "data": dias_atras(29), "descricao": "Compra antiga",
        "valor": -100.0, "categoria_id": categoria_id,
    }, headers=headers_autenticado)

    r = client.put(f"/contas/{conta_id}/inicio", json={
        "data": dias_atras(14), "saldo_real": 1000.0,
    }, headers=headers_autenticado)
    assert r.status_code == 400


def test_criar_movimento_antes_da_reconciliacao_mais_antiga_falha(client, headers_autenticado, conta_id, categoria_id):
    r = client.post("/movimentos", json={
        "conta_id": conta_id, "data": dias_atras(10), "descricao": "Compra antiga",
        "valor": -50.0, "categoria_id": categoria_id,
    }, headers=headers_autenticado)
    assert r.status_code == 400


def test_criar_movimento_apos_recuar_ancora_funciona(client, headers_autenticado, conta_id, categoria_id):
    recuar_ancora(client, headers_autenticado, conta_id, dias_atras(30))

    r = client.post("/movimentos", json={
        "conta_id": conta_id, "data": dias_atras(10), "descricao": "Compra antiga",
        "valor": -50.0, "categoria_id": categoria_id,
    }, headers=headers_autenticado)
    assert r.status_code == 200


# ═══════════════════════════════════════════════════════════
# Conta/reconciliação inexistente (ids inválidos ou de outro utilizador)
# ═══════════════════════════════════════════════════════════
def test_criar_ajuste_saldo_conta_inexistente_falha(client, headers_autenticado):
    r = client.post("/contas/id-que-nao-existe/ajustes-saldo", json={
        "data": dias_atras(1), "saldo_real": 500.0,
    }, headers=headers_autenticado)
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "CONTA_NAO_ENCONTRADA"


def test_editar_ajuste_saldo_inexistente_falha(client, headers_autenticado):
    r = client.put("/ajustes-saldo/999999", json={
        "data": dias_atras(1), "saldo_real": 500.0,
    }, headers=headers_autenticado)
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "RECONCILIACAO_NAO_ENCONTRADA"


def test_editar_ajuste_saldo_com_sucesso_atualiza_valor(client, headers_autenticado, conta_id):
    """Só havia teste do caminho "reconciliação inexistente" — faltava confirmar que
    editar uma reconciliação a sério (id real) chega a actualizar o valor guardado."""
    client.post(f"/contas/{conta_id}/ajustes-saldo", json={
        "data": hoje(), "saldo_real": 1200.0,
    }, headers=headers_autenticado)
    ajuste_id = client.get(f"/contas/{conta_id}/ajustes-saldo", headers=headers_autenticado).json()[0]["id"]

    r = client.put(f"/ajustes-saldo/{ajuste_id}", json={
        "data": hoje(), "saldo_real": 1500.0,
    }, headers=headers_autenticado)
    assert r.status_code == 200

    ajustes = client.get(f"/contas/{conta_id}/ajustes-saldo", headers=headers_autenticado).json()
    assert ajustes[0]["saldo_real"] == 1500.0


def test_eliminar_ajuste_saldo_inexistente_falha(client, headers_autenticado):
    r = client.delete("/ajustes-saldo/999999", headers=headers_autenticado)
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "RECONCILIACAO_NAO_ENCONTRADA"
