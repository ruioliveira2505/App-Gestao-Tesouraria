from tests.helpers import hoje, dias_atras, id_categoria, criar_movimento


def recuar_reconciliacao(client, headers, conta_id, data):
    ajustes = client.get(f"/contas/{conta_id}/ajustes-saldo", headers=headers).json()
    ajuste_id = ajustes[0]["id"]
    r = client.put(f"/ajustes-saldo/{ajuste_id}", json={
        "data": data, "saldo_real": 1000.0,
    }, headers=headers)
    assert r.status_code == 200


# ═══════════════════════════════════════════════════════════
# /stats/mensal
# ═══════════════════════════════════════════════════════════
def test_stats_mensal_agrega_entradas_e_saidas(client, headers_autenticado, conta_id):
    salario  = id_categoria(client, headers_autenticado, "Trabalho", "Salário")
    super_   = id_categoria(client, headers_autenticado, "Alimentação", "Supermercado")

    criar_movimento(client, headers_autenticado, conta_id, salario, 2000.0)
    criar_movimento(client, headers_autenticado, conta_id, super_, -150.0)

    r = client.get("/stats/mensal", headers=headers_autenticado).json()
    assert len(r) == 1
    mes = r[0]
    assert mes["entradas"] == 2000.0
    assert mes["saidas"] == 150.0
    assert mes["liquido"] == 1850.0


def test_stats_mensal_separa_por_mes(client, headers_autenticado, conta_id):
    recuar_reconciliacao(client, headers_autenticado, conta_id, dias_atras(50))
    super_ = id_categoria(client, headers_autenticado, "Alimentação", "Supermercado")
    criar_movimento(client, headers_autenticado, conta_id, super_, -50.0, data=dias_atras(45))
    criar_movimento(client, headers_autenticado, conta_id, super_, -30.0, data=hoje())

    r = client.get("/stats/mensal", headers=headers_autenticado).json()
    assert len(r) == 2


def test_stats_mensal_filtra_por_periodo(client, headers_autenticado, conta_id):
    recuar_reconciliacao(client, headers_autenticado, conta_id, dias_atras(50))
    super_ = id_categoria(client, headers_autenticado, "Alimentação", "Supermercado")
    criar_movimento(client, headers_autenticado, conta_id, super_, -50.0, data=dias_atras(45))
    criar_movimento(client, headers_autenticado, conta_id, super_, -30.0, data=hoje())

    r = client.get(f"/stats/mensal?data_de={dias_atras(10)}&data_ate={hoje()}", headers=headers_autenticado).json()
    assert len(r) == 1
    assert r[0]["saidas"] == 30.0


# ═══════════════════════════════════════════════════════════
# /stats/categorias
# ═══════════════════════════════════════════════════════════
def test_stats_categorias_calcula_percentagens_corretamente(client, headers_autenticado, conta_id):
    super_ = id_categoria(client, headers_autenticado, "Alimentação", "Supermercado")
    rest   = id_categoria(client, headers_autenticado, "Alimentação", "Restaurantes e Cafés")

    criar_movimento(client, headers_autenticado, conta_id, super_, -75.0)
    criar_movimento(client, headers_autenticado, conta_id, rest, -25.0)

    r = client.get("/stats/categorias", headers=headers_autenticado).json()
    saidas = {c["categoria"]: c for c in r if not c["eh_recebimento"]}

    assert saidas["Alimentação > Supermercado"]["total"] == 75.0
    assert saidas["Alimentação > Supermercado"]["percentagem"] == 75.0
    assert saidas["Alimentação > Restaurantes e Cafés"]["percentagem"] == 25.0


def test_stats_categorias_entradas_e_saidas_tem_bases_de_percentagem_separadas(client, headers_autenticado, conta_id):
    salario = id_categoria(client, headers_autenticado, "Trabalho", "Salário")
    super_  = id_categoria(client, headers_autenticado, "Alimentação", "Supermercado")

    criar_movimento(client, headers_autenticado, conta_id, salario, 1000.0)
    criar_movimento(client, headers_autenticado, conta_id, super_, -100.0)

    r = client.get("/stats/categorias", headers=headers_autenticado).json()
    entrada = next(c for c in r if c["eh_recebimento"])
    saida   = next(c for c in r if not c["eh_recebimento"])

    assert entrada["percentagem"] == 100.0
    assert saida["percentagem"] == 100.0


# ═══════════════════════════════════════════════════════════
# /stats/grupos
# ═══════════════════════════════════════════════════════════
def test_stats_grupos_agrupa_subcategorias_dentro_do_grupo(client, headers_autenticado, conta_id):
    super_ = id_categoria(client, headers_autenticado, "Alimentação", "Supermercado")
    rest   = id_categoria(client, headers_autenticado, "Alimentação", "Restaurantes e Cafés")

    criar_movimento(client, headers_autenticado, conta_id, super_, -60.0)
    criar_movimento(client, headers_autenticado, conta_id, rest, -40.0)

    r = client.get("/stats/grupos", headers=headers_autenticado).json()
    alimentacao = next(g for g in r if g["grupo"] == "Alimentação")

    assert alimentacao["total"] == 100.0
    assert len(alimentacao["subcategorias"]) == 2
    assert alimentacao["subcategorias"][0]["categoria"] == "Supermercado"  # ordenado por total desc


def test_stats_grupos_ordenados_por_total_descendente(client, headers_autenticado, conta_id):
    salario = id_categoria(client, headers_autenticado, "Trabalho", "Salário")
    juros   = id_categoria(client, headers_autenticado, "Investimentos", "Juros")

    criar_movimento(client, headers_autenticado, conta_id, juros, 50.0)
    criar_movimento(client, headers_autenticado, conta_id, salario, 2000.0)

    r = client.get("/stats/grupos", headers=headers_autenticado).json()
    entradas = [g for g in r if g["eh_recebimento"]]
    assert entradas[0]["grupo"] == "Trabalho"


# ═══════════════════════════════════════════════════════════
# /stats/saldo-diario
# ═══════════════════════════════════════════════════════════
def test_saldo_diario_reflete_saldo_inicial_sem_movimentos(client, headers_autenticado, conta_id):
    r = client.get("/stats/saldo-diario", headers=headers_autenticado).json()
    assert len(r) >= 1
    assert r[-1]["saldo"] == 1000.0


def test_saldo_diario_acumula_movimentos_ao_longo_dos_dias(client, headers_autenticado, conta_id):
    recuar_reconciliacao(client, headers_autenticado, conta_id, dias_atras(5))
    super_ = id_categoria(client, headers_autenticado, "Alimentação", "Supermercado")
    criar_movimento(client, headers_autenticado, conta_id, super_, -100.0, data=dias_atras(2))
    criar_movimento(client, headers_autenticado, conta_id, super_, -50.0, data=hoje())

    r = client.get("/stats/saldo-diario", headers=headers_autenticado).json()
    por_data = {p["data"]: p["saldo"] for p in r}

    assert por_data[dias_atras(3)] == 1000.0
    assert por_data[dias_atras(2)] == 900.0
    assert por_data[hoje()] == 850.0


def test_saldo_diario_filtra_por_conta(client, headers_autenticado, conta_id):
    client.post("/contas", json={
        "nome": "Conta B", "banco": "BPI", "tipo": "corrente",
        "iban": "PT5022222222222222222222222", "moeda": "EUR", "saldo": 500.0,
    }, headers=headers_autenticado)
    contas = client.get("/contas", headers=headers_autenticado).json()
    conta_b_id = next(c["id"] for c in contas if c["nome"] == "Conta B")

    r = client.get(f"/stats/saldo-diario?conta_id={conta_b_id}", headers=headers_autenticado).json()
    assert r[-1]["saldo"] == 500.0


# ═══════════════════════════════════════════════════════════
# /stats/recorrentes
# ═══════════════════════════════════════════════════════════
def test_recorrentes_deteta_padrao_regular(client, headers_autenticado, conta_id):
    recuar_reconciliacao(client, headers_autenticado, conta_id, dias_atras(65))
    netflix = id_categoria(client, headers_autenticado, "Entretenimento", "Subscrições")

    criar_movimento(client, headers_autenticado, conta_id, netflix, -17.99, data=dias_atras(60), descricao="Netflix")
    criar_movimento(client, headers_autenticado, conta_id, netflix, -17.99, data=dias_atras(30), descricao="Netflix")
    criar_movimento(client, headers_autenticado, conta_id, netflix, -17.99, data=hoje(), descricao="Netflix")

    r = client.get("/stats/recorrentes", headers=headers_autenticado).json()
    netflix_rec = next(x for x in r if x["descricao"] == "Netflix")

    assert netflix_rec["ocorrencias"] == 3
    assert netflix_rec["regular"] is True
    assert netflix_rec["valor_medio"] == -17.99
    assert netflix_rec["intervalo_medio_dias"] == 30


def test_recorrentes_ignora_descricoes_com_uma_so_ocorrencia(client, headers_autenticado, conta_id):
    super_ = id_categoria(client, headers_autenticado, "Alimentação", "Supermercado")
    criar_movimento(client, headers_autenticado, conta_id, super_, -45.0, descricao="Compra Única")

    r = client.get("/stats/recorrentes", headers=headers_autenticado).json()
    assert not any(x["descricao"] == "Compra Única" for x in r)


def test_recorrentes_marca_padrao_irregular_como_nao_regular(client, headers_autenticado, conta_id):
    recuar_reconciliacao(client, headers_autenticado, conta_id, dias_atras(90))
    aluguer = id_categoria(client, headers_autenticado, "Habitação", "Renda")

    criar_movimento(client, headers_autenticado, conta_id, aluguer, -650.0, data=dias_atras(85), descricao="Renda Irregular")
    criar_movimento(client, headers_autenticado, conta_id, aluguer, -650.0, data=dias_atras(70), descricao="Renda Irregular")
    criar_movimento(client, headers_autenticado, conta_id, aluguer, -650.0, data=dias_atras(0), descricao="Renda Irregular")

    r = client.get("/stats/recorrentes", headers=headers_autenticado).json()
    renda = next(x for x in r if x["descricao"] == "Renda Irregular")
    assert renda["regular"] is False


def test_recorrentes_ignora_entradas_so_considera_saidas(client, headers_autenticado, conta_id):
    recuar_reconciliacao(client, headers_autenticado, conta_id, dias_atras(35))
    salario = id_categoria(client, headers_autenticado, "Trabalho", "Salário")
    criar_movimento(client, headers_autenticado, conta_id, salario, 2000.0, data=dias_atras(30), descricao="Salário")
    criar_movimento(client, headers_autenticado, conta_id, salario, 2000.0, data=hoje(), descricao="Salário")

    r = client.get("/stats/recorrentes", headers=headers_autenticado).json()
    assert not any(x["descricao"] == "Salário" for x in r)


def test_recorrentes_de_outro_utilizador_nao_aparecem(client, headers_autenticado, conta_id):
    recuar_reconciliacao(client, headers_autenticado, conta_id, dias_atras(35))
    netflix = id_categoria(client, headers_autenticado, "Entretenimento", "Subscrições")
    criar_movimento(client, headers_autenticado, conta_id, netflix, -17.99, data=dias_atras(30), descricao="Netflix Privado")
    criar_movimento(client, headers_autenticado, conta_id, netflix, -17.99, data=hoje(), descricao="Netflix Privado")

    client.post("/registro", json={"nome": "Outro", "email": "outro@exemplo.com", "password": "senha123"})
    r_outro = client.post("/login", json={"email": "outro@exemplo.com", "password": "senha123"})
    headers_outro = {"Authorization": f"Bearer {r_outro.json()['token']}"}

    r = client.get("/stats/recorrentes", headers=headers_outro).json()
    assert r == []