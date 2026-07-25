from datetime import date, timedelta


def hoje():
    return str(date.today())


def dias_atras(n):
    return str(date.today() - timedelta(days=n))


def dias_a_frente(n):
    return str(date.today() + timedelta(days=n))


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


def grupo_por_direcao(client, headers, nome_grupo, eh_recebimento):
    arvore = client.get("/categorias/arvore", headers=headers).json()
    return next(g for g in arvore if g["nome"] == nome_grupo and g["eh_recebimento"] == eh_recebimento)


def recuar_ancora(client, headers, conta_id, data_ancora, saldo_real=1000.0, confirmar=False):
    # a API de /inicio recebe a Data de Início de Movimentos (âncora + 1 dia), não a âncora em bruto
    inicio_movimentos = str(date.fromisoformat(data_ancora) + timedelta(days=1))
    r = client.put(
        f"/contas/{conta_id}/inicio?confirmar={str(confirmar).lower()}",
        json={"data": inicio_movimentos, "saldo_real": saldo_real},
        headers=headers,
    )
    assert r.status_code == 200, r.json()
    return r