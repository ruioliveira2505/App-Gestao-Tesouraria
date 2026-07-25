from tests.helpers import dias_a_frente, dias_atras, hoje


def conta_exemplo(**overrides):
    base = {
        "nome": "Conta Principal", "banco": "CGD", "tipo": "corrente",
        "iban": "PT50000000000000000000000", "moeda": "EUR", "saldo": 1000.0,
        "data": dias_atras(1),
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


def test_eliminar_conta_com_movimentos_pede_confirmacao(client, headers_autenticado, categoria_id):
    client.post("/contas", json=conta_exemplo(), headers=headers_autenticado)
    conta_id = client.get("/contas", headers=headers_autenticado).json()[0]["id"]
    client.post("/movimentos", json={
        "conta_id": conta_id, "data": hoje(), "descricao": "Teste",
        "valor": -50.0, "categoria_id": categoria_id,
    }, headers=headers_autenticado)
    r = client.delete(f"/contas/{conta_id}", headers=headers_autenticado)
    assert r.status_code == 400
    detail = r.json()["detail"]
    assert detail["code"] == "CONTA_COM_MOVIMENTOS"
    # ctx exposto em bruto (não só a mensagem já formatada em português) — é o que
    # permite ao frontend construir a frase em inglês com o número certo, sem depender
    # do texto português (ver static/js/i18n.js::ERROS_TRADUCOES.en.CONTA_COM_MOVIMENTOS).
    assert detail["ctx"] == {"n": 1}


def test_eliminar_conta_com_forcar_remove_tudo(client, headers_autenticado, categoria_id):
    client.post("/contas", json=conta_exemplo(), headers=headers_autenticado)
    conta_id = client.get("/contas", headers=headers_autenticado).json()[0]["id"]
    client.post("/movimentos", json={
        "conta_id": conta_id, "data": hoje(), "descricao": "Teste",
        "valor": -50.0, "categoria_id": categoria_id,
    }, headers=headers_autenticado)
    r = client.delete(f"/contas/{conta_id}?forcar=true", headers=headers_autenticado)
    assert r.status_code == 200
    assert client.get("/movimentos", headers=headers_autenticado).json() == []


# ═══════════════════════════════════════════════════════════
# Validação de campos
# ═══════════════════════════════════════════════════════════
def test_criar_conta_com_nome_vazio_falha(client, headers_autenticado):
    r = client.post("/contas", json=conta_exemplo(nome=""), headers=headers_autenticado)
    assert r.status_code == 422


def test_criar_conta_com_iban_demasiado_longo_falha(client, headers_autenticado):
    r = client.post("/contas", json=conta_exemplo(iban="PT" + "0" * 40), headers=headers_autenticado)
    assert r.status_code == 422


def test_criar_conta_com_data_malformada_falha_com_422(client, headers_autenticado):
    """Antes de `data` ser `date` no schema (em vez de `str`), isto só era apanhado tarde,
    ou nem isso — comparação de strings não avisa de nada."""
    r = client.post("/contas", json=conta_exemplo(data="31-02-2026"), headers=headers_autenticado)
    assert r.status_code == 422


def test_saldo_em_data_com_data_malformada_falha_com_422(client, headers_autenticado, conta_id):
    r = client.get(f"/contas/{conta_id}/saldo-em-data?data=nao-e-uma-data", headers=headers_autenticado)
    assert r.status_code == 422


def test_criar_conta_com_data_futura_falha(client, headers_autenticado):
    r = client.post("/contas", json=conta_exemplo(data=dias_a_frente(1)), headers=headers_autenticado)
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "DATA_FUTURA"


# ═══════════════════════════════════════════════════════════
# Conta/reconciliação inexistente (ids inválidos ou de outro utilizador)
# ═══════════════════════════════════════════════════════════
def test_obter_inicio_conta_inexistente_falha(client, headers_autenticado):
    r = client.get("/contas/id-que-nao-existe/inicio", headers=headers_autenticado)
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "CONTA_NAO_ENCONTRADA"


def test_editar_inicio_conta_inexistente_falha(client, headers_autenticado):
    r = client.put(
        "/contas/id-que-nao-existe/inicio",
        json={"data": hoje(), "saldo_real": 100.0}, headers=headers_autenticado,
    )
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "CONTA_NAO_ENCONTRADA"


def test_saldo_em_data_conta_inexistente_falha(client, headers_autenticado):
    r = client.get(f"/contas/id-que-nao-existe/saldo-em-data?data={hoje()}", headers=headers_autenticado)
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "CONTA_NAO_ENCONTRADA"


def test_saldo_em_data_antes_da_ancora_falha(client, headers_autenticado):
    client.post("/contas", json=conta_exemplo(data=dias_atras(5)), headers=headers_autenticado)
    conta_id = client.get("/contas", headers=headers_autenticado).json()[0]["id"]

    r = client.get(f"/contas/{conta_id}/saldo-em-data?data={dias_atras(10)}", headers=headers_autenticado)
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "SEM_RECONCILIACAO_ANTERIOR"


def test_saldo_em_data_devolve_saldo_correto(client, headers_autenticado, conta_id, categoria_id):
    """Só havia testes dos caminhos de erro (data malformada, conta inexistente, antes da
    âncora) — faltava confirmar que, no caminho normal, o saldo devolvido é mesmo a âncora
    mais os movimentos até à data pedida."""
    client.post("/movimentos", json={
        "conta_id": conta_id, "data": hoje(), "descricao": "Compra",
        "valor": -50.0, "categoria_id": categoria_id,
    }, headers=headers_autenticado)

    r = client.get(f"/contas/{conta_id}/saldo-em-data?data={hoje()}", headers=headers_autenticado)
    assert r.status_code == 200
    assert r.json()["saldo"] == 950.0


def test_editar_inicio_conta_que_ultrapassa_reconciliacoes_pede_confirmacao_e_elimina(client, headers_autenticado):
    client.post("/contas", json=conta_exemplo(data=dias_atras(30)), headers=headers_autenticado)
    conta_id = client.get("/contas", headers=headers_autenticado).json()[0]["id"]

    client.post(f"/contas/{conta_id}/ajustes-saldo", json={
        "data": dias_atras(15), "saldo_real": 900.0,
    }, headers=headers_autenticado)

    nova_data_inicio = dias_atras(5)
    r = client.put(f"/contas/{conta_id}/inicio", json={
        "data": nova_data_inicio, "saldo_real": 800.0,
    }, headers=headers_autenticado)
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "INICIO_ULTRAPASSA_RECONCILIACOES"

    r = client.put(f"/contas/{conta_id}/inicio?confirmar=true", json={
        "data": nova_data_inicio, "saldo_real": 800.0,
    }, headers=headers_autenticado)
    assert r.status_code == 200
    assert client.get(f"/contas/{conta_id}/ajustes-saldo", headers=headers_autenticado).json() == []