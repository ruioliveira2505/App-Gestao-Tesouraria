from app.db.database import get_connection, release_connection
from tests.helpers import hoje


def arvore(client, headers):
    return client.get("/categorias/arvore", headers=headers).json()


def grupo(client, headers, nome):
    return next(g for g in arvore(client, headers) if g["nome"] == nome)


# ═══════════════════════════════════════════════════════════
# GET /categorias e /categorias/arvore
# ═══════════════════════════════════════════════════════════
def test_listar_categorias_devolve_apenas_folhas(client, headers_autenticado):
    categorias = client.get("/categorias", headers=headers_autenticado).json()
    assert len(categorias) > 0
    for c in categorias:
        assert "grupo" in c and "eh_recebimento" in c


def test_listar_categorias_inclui_slug(client, headers_autenticado):
    categorias = client.get("/categorias", headers=headers_autenticado).json()
    supermercado = next(c for c in categorias if c["nome"] == "Supermercado")
    assert supermercado["slug"] == "out.alimentacao.supermercado"


def test_arvore_tem_grupos_padrao_com_subcategorias(client, headers_autenticado):
    a = arvore(client, headers_autenticado)
    assert any(g["nome"] == "Trabalho" for g in a)
    trabalho = grupo(client, headers_autenticado, "Trabalho")
    assert any(c["nome"] == "Salário" for c in trabalho["categorias"])


def test_arvore_tem_todos_os_grupos_com_subcategorias_corretas(client, headers_autenticado):
    """Cobertura completa contra ARVORE_PADRAO — em particular, confirma que o seed em
    bloco (services/categorias_seed.py) associa cada categoria-folha ao grupo certo e não
    troca nada entre grupos (haveria disto na 1ª subcategoria de cada grupo se a
    correspondência entre INSERT em bloco e RETURNING não preservasse a ordem)."""
    from app.services.categorias_seed import ARVORE_PADRAO

    a = arvore(client, headers_autenticado)
    # há dois grupos "Transferências Próprias" (um de entradas, outro de saídas) —
    # por isso agrupa-se por (nome, eh_recebimento), não só por nome.
    grupos_por_chave = {}
    for g in a:
        grupos_por_chave.setdefault((g["nome"], g["eh_recebimento"]), []).append(g)

    assert len(a) == len(ARVORE_PADRAO)
    for nome_grupo, eh_recebimento, categorias_esperadas in ARVORE_PADRAO:
        candidatos = grupos_por_chave[(nome_grupo, eh_recebimento)]
        # cada par (nome, eh_recebimento) aparece uma só vez, excepto quando o próprio
        # ARVORE_PADRAO o repete (não é o caso) — assume-se 1 grupo por chave
        assert len(candidatos) == 1, f"grupo duplicado ou em falta: {nome_grupo} (eh_recebimento={eh_recebimento})"
        nomes_reais = {c["nome"] for c in candidatos[0]["categorias"]}
        assert nomes_reais == set(categorias_esperadas), f"subcategorias erradas em {nome_grupo} (eh_recebimento={eh_recebimento})"


def test_categorias_por_omissao_tem_slug_unico_e_nao_nulo(client, headers_autenticado):
    """slug é o que permite ao frontend traduzir o nome de uma categoria de sistema sem
    depender do texto actual (ver migração 0014_slug_categorias.sql) — todas as categorias
    por omissão têm de ter um, e nenhum se pode repetir dentro da mesma conta."""
    a = arvore(client, headers_autenticado)
    slugs = []
    for g in a:
        assert g["slug"] is not None, f"grupo sem slug: {g['nome']}"
        slugs.append(g["slug"])
        for c in g["categorias"]:
            assert c["slug"] is not None, f"categoria sem slug: {g['nome']} > {c['nome']}"
            slugs.append(c["slug"])

    assert len(slugs) == len(set(slugs)), "há slugs repetidos"
    # amostra — confirma o formato "<in|out>.<grupo>[.<categoria>]"
    alimentacao = grupo(client, headers_autenticado, "Alimentação")
    assert alimentacao["slug"] == "out.alimentacao"
    supermercado = next(c for c in alimentacao["categorias"] if c["nome"] == "Supermercado")
    assert supermercado["slug"] == "out.alimentacao.supermercado"


def test_slug_sobrevive_a_renomeacao_da_categoria(client, headers_autenticado):
    alimentacao = grupo(client, headers_autenticado, "Alimentação")
    supermercado = next(c for c in alimentacao["categorias"] if c["nome"] == "Supermercado")

    r = client.put(f"/categorias/{supermercado['id']}", json={"nome": "Compras de Comida"}, headers=headers_autenticado)
    assert r.status_code == 200

    a = arvore(client, headers_autenticado)
    alimentacao2 = next(g for g in a if g["slug"] == "out.alimentacao")
    renomeada = next(c for c in alimentacao2["categorias"] if c["nome"] == "Compras de Comida")
    assert renomeada["slug"] == "out.alimentacao.supermercado"


def test_categoria_e_grupo_criados_pelo_utilizador_nao_tem_slug(client, headers_autenticado):
    client.post("/categorias", json={"nome": "Grupo Pessoal", "eh_recebimento": False}, headers=headers_autenticado)
    grupo_pessoal = grupo(client, headers_autenticado, "Grupo Pessoal")
    assert grupo_pessoal["slug"] is None

    client.post("/categorias", json={"nome": "Categoria Pessoal", "parent_id": grupo_pessoal["id"]}, headers=headers_autenticado)
    grupo_pessoal2 = grupo(client, headers_autenticado, "Grupo Pessoal")
    categoria_pessoal = next(c for c in grupo_pessoal2["categorias"] if c["nome"] == "Categoria Pessoal")
    assert categoria_pessoal["slug"] is None


def test_categorias_de_outro_utilizador_nao_aparecem(client, headers_autenticado):
    client.post("/registro", json={"nome": "Outro", "email": "outro@exemplo.com", "password": "senha123"})
    r_outro = client.post("/login", json={"email": "outro@exemplo.com", "password": "senha123"})
    headers_outro = {"Authorization": f"Bearer {r_outro.json()['token']}"}

    ids_ana   = {c["id"] for c in client.get("/categorias", headers=headers_autenticado).json()}
    ids_outro = {c["id"] for c in client.get("/categorias", headers=headers_outro).json()}
    assert ids_ana.isdisjoint(ids_outro)


# ═══════════════════════════════════════════════════════════
# POST /categorias
# ═══════════════════════════════════════════════════════════
def test_criar_grupo_com_sucesso(client, headers_autenticado):
    r = client.post("/categorias", json={"nome": "Hobbies", "eh_recebimento": False}, headers=headers_autenticado)
    assert r.status_code == 200
    assert any(g["nome"] == "Hobbies" for g in arvore(client, headers_autenticado))


def test_criar_grupo_sem_indicar_direcao_falha(client, headers_autenticado):
    r = client.post("/categorias", json={"nome": "Sem Direção"}, headers=headers_autenticado)
    assert r.status_code == 400


def test_criar_subcategoria_com_sucesso(client, headers_autenticado):
    trabalho = grupo(client, headers_autenticado, "Trabalho")
    r = client.post("/categorias", json={"nome": "Bónus", "parent_id": trabalho["id"]}, headers=headers_autenticado)
    assert r.status_code == 200
    trabalho2 = grupo(client, headers_autenticado, "Trabalho")
    assert any(c["nome"] == "Bónus" for c in trabalho2["categorias"])


def test_subcategoria_criada_herda_direcao_do_grupo(client, headers_autenticado):
    despesa = next(g for g in arvore(client, headers_autenticado) if not g["eh_recebimento"])
    client.post("/categorias", json={"nome": "Nova Despesa", "parent_id": despesa["id"]}, headers=headers_autenticado)
    nova = next(c for c in client.get("/categorias", headers=headers_autenticado).json() if c["nome"] == "Nova Despesa")
    assert nova["eh_recebimento"] is False


def test_criar_subcategoria_com_parent_id_inexistente_deveria_dar_erro_amigavel(client, headers_autenticado):
    r = client.post("/categorias", json={"nome": "X", "parent_id": 999999}, headers=headers_autenticado)
    assert r.status_code in (400, 404)


def test_criar_subcategoria_com_parent_id_de_outro_utilizador_deveria_falhar(client, headers_autenticado):
    client.post("/registro", json={"nome": "Outro", "email": "outro@exemplo.com", "password": "senha123"})
    r_outro = client.post("/login", json={"email": "outro@exemplo.com", "password": "senha123"})
    headers_outro = {"Authorization": f"Bearer {r_outro.json()['token']}"}
    grupo_de_outro = arvore(client, headers_outro)[0]["id"]

    r = client.post("/categorias", json={"nome": "Infiltrada", "parent_id": grupo_de_outro}, headers=headers_autenticado)
    assert r.status_code in (400, 403, 404)


# ═══════════════════════════════════════════════════════════
# PUT /categorias/{id}
# ═══════════════════════════════════════════════════════════
def test_editar_nome_de_grupo(client, headers_autenticado):
    tech = grupo(client, headers_autenticado, "Tecnologia")
    r = client.put(f"/categorias/{tech['id']}", json={"nome": "Tech & Gadgets"}, headers=headers_autenticado)
    assert r.status_code == 200
    assert any(g["nome"] == "Tech & Gadgets" for g in arvore(client, headers_autenticado))


def test_editar_nome_de_categoria_folha(client, headers_autenticado):
    tech = grupo(client, headers_autenticado, "Tecnologia")
    hardware = next(c for c in tech["categorias"] if c["nome"] == "Hardware")
    r = client.put(f"/categorias/{hardware['id']}", json={"nome": "Equipamento"}, headers=headers_autenticado)
    assert r.status_code == 200


def test_editar_categoria_inexistente_falha(client, headers_autenticado):
    r = client.put("/categorias/999999", json={"nome": "X"}, headers=headers_autenticado)
    assert r.status_code == 404


def test_mover_grupo_para_dentro_de_outro_grupo_falha(client, headers_autenticado):
    tech = grupo(client, headers_autenticado, "Tecnologia")
    ent = grupo(client, headers_autenticado, "Entretenimento")
    r = client.put(f"/categorias/{tech['id']}", json={"nome": "Tecnologia", "parent_id": ent["id"]}, headers=headers_autenticado)
    assert r.status_code == 400


def test_mover_categoria_para_outro_grupo(client, headers_autenticado):
    tech = grupo(client, headers_autenticado, "Tecnologia")
    ent  = grupo(client, headers_autenticado, "Entretenimento")
    software = next(c for c in tech["categorias"] if c["nome"] == "Software")

    r = client.put(f"/categorias/{software['id']}", json={"nome": "Software", "parent_id": ent["id"]}, headers=headers_autenticado)
    assert r.status_code == 200
    ent2 = grupo(client, headers_autenticado, "Entretenimento")
    assert any(c["nome"] == "Software" for c in ent2["categorias"])


def test_reordenar_categorias_grava_a_nova_ordem(client, headers_autenticado):
    tech = grupo(client, headers_autenticado, "Tecnologia")
    ids_originais = [c["id"] for c in tech["categorias"]]
    nova_ordem = list(reversed(ids_originais))

    r = client.put("/categorias/reordenar", json={"ids": nova_ordem}, headers=headers_autenticado)
    assert r.status_code == 200

    tech2 = grupo(client, headers_autenticado, "Tecnologia")
    assert [c["id"] for c in tech2["categorias"]] == nova_ordem


def test_reordenar_categorias_nao_mexe_em_categorias_de_outro_utilizador(client, headers_autenticado):
    tech = grupo(client, headers_autenticado, "Tecnologia")
    ids_originais = [c["id"] for c in tech["categorias"]]
    nova_ordem = list(reversed(ids_originais))

    client.post("/registro", json={"nome": "Outro", "email": "outro-reordenar@exemplo.com", "password": "senha123"})
    r_outro = client.post("/login", json={"email": "outro-reordenar@exemplo.com", "password": "senha123"})
    headers_outro = {"Authorization": f"Bearer {r_outro.json()['token']}"}

    # tenta reordenar os ids de outro utilizador através da própria sessão — a query
    # (UPDATE ... FROM VALUES) tem de continuar a filtrar por utilizador_id, tal como o
    # ciclo de UPDATEs que substituiu.
    r = client.put("/categorias/reordenar", json={"ids": nova_ordem}, headers=headers_outro)
    assert r.status_code == 200

    tech_depois = grupo(client, headers_autenticado, "Tecnologia")
    assert [c["id"] for c in tech_depois["categorias"]] == ids_originais


# ═══════════════════════════════════════════════════════════
# DELETE /categorias/{id} — categoria folha
# ═══════════════════════════════════════════════════════════
def test_eliminar_categoria_folha_sem_movimentos(client, headers_autenticado):
    tech = grupo(client, headers_autenticado, "Tecnologia")
    outros = next(c for c in tech["categorias"] if c["nome"] == "Outros")
    r = client.delete(f"/categorias/{outros['id']}", headers=headers_autenticado)
    assert r.status_code == 200


def test_eliminar_categoria_folha_sem_movimentos_mas_com_cache_aprendida(client, headers_autenticado, conta_id):
    tech = grupo(client, headers_autenticado, "Tecnologia")
    hardware = next(c for c in tech["categorias"] if c["nome"] == "Hardware")

    client.post("/movimentos", json={
        "conta_id": conta_id, "data": hoje(), "descricao": "Teclado",
        "valor": -50.0, "categoria_id": hardware["id"],
    }, headers=headers_autenticado)
    movimento_id = client.get("/movimentos", headers=headers_autenticado).json()[0]["id"]

    # editar (não criar) é o que escreve em categorias_aprendidas
    client.put(f"/movimentos/{movimento_id}", json={
        "conta_id": conta_id, "data": hoje(), "descricao": "Teclado",
        "valor": -50.0, "categoria_id": hardware["id"],
    }, headers=headers_autenticado)
    client.delete(f"/movimentos/{movimento_id}", headers=headers_autenticado)

    r = client.delete(f"/categorias/{hardware['id']}", headers=headers_autenticado)
    assert r.status_code == 200

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM categorias_aprendidas WHERE categoria_id = %s", (hardware["id"],))
    assert cursor.fetchone()[0] == 0
    cursor.close()
    release_connection(conn)


def test_eliminar_categoria_folha_com_movimentos_pede_confirmacao(client, headers_autenticado, conta_id):
    tech = grupo(client, headers_autenticado, "Tecnologia")
    hardware = next(c for c in tech["categorias"] if c["nome"] == "Hardware")
    client.post("/movimentos", json={
        "conta_id": conta_id, "data": hoje(), "descricao": "Teclado",
        "valor": -50.0, "categoria_id": hardware["id"],
    }, headers=headers_autenticado)

    r = client.delete(f"/categorias/{hardware['id']}", headers=headers_autenticado)
    assert r.status_code == 400
    detail = r.json()["detail"]
    assert detail["code"] == "CATEGORIA_COM_MOVIMENTOS"
    # ctx em bruto (não só a mensagem já em português) — ver
    # static/js/i18n.js::ERROS_TRADUCOES.en.CATEGORIA_COM_MOVIMENTOS.
    assert detail["ctx"] == {"n": 1}


def test_eliminar_categoria_folha_com_migracao_reatribui_movimentos(client, headers_autenticado, conta_id):
    tech = grupo(client, headers_autenticado, "Tecnologia")
    origem  = next(c for c in tech["categorias"] if c["nome"] == "Hardware")
    destino = next(c for c in tech["categorias"] if c["nome"] == "Software")

    client.post("/movimentos", json={
        "conta_id": conta_id, "data": hoje(), "descricao": "Teclado",
        "valor": -50.0, "categoria_id": origem["id"],
    }, headers=headers_autenticado)

    r = client.delete(f"/categorias/{origem['id']}?migrar_para_id={destino['id']}", headers=headers_autenticado)
    assert r.status_code == 200
    assert client.get("/movimentos", headers=headers_autenticado).json()[0]["categoria_id"] == destino["id"]


def test_eliminar_categoria_folha_com_forcar_remove_movimentos(client, headers_autenticado, conta_id):
    tech = grupo(client, headers_autenticado, "Tecnologia")
    hardware = next(c for c in tech["categorias"] if c["nome"] == "Hardware")
    client.post("/movimentos", json={
        "conta_id": conta_id, "data": hoje(), "descricao": "Teclado",
        "valor": -50.0, "categoria_id": hardware["id"],
    }, headers=headers_autenticado)

    r = client.delete(f"/categorias/{hardware['id']}?forcar=true", headers=headers_autenticado)
    assert r.status_code == 200
    assert client.get("/movimentos", headers=headers_autenticado).json() == []


def test_eliminar_categoria_com_migrar_para_id_de_outro_utilizador_deveria_falhar(client, headers_autenticado, conta_id):
    client.post("/registro", json={"nome": "Outro", "email": "outro@exemplo.com", "password": "senha123"})
    r_outro = client.post("/login", json={"email": "outro@exemplo.com", "password": "senha123"})
    headers_outro = {"Authorization": f"Bearer {r_outro.json()['token']}"}
    categoria_de_outro = client.get("/categorias", headers=headers_outro).json()[0]["id"]

    tech = grupo(client, headers_autenticado, "Tecnologia")
    hardware = next(c for c in tech["categorias"] if c["nome"] == "Hardware")
    client.post("/movimentos", json={
        "conta_id": conta_id, "data": hoje(), "descricao": "Teclado",
        "valor": -50.0, "categoria_id": hardware["id"],
    }, headers=headers_autenticado)

    r = client.delete(f"/categorias/{hardware['id']}?migrar_para_id={categoria_de_outro}", headers=headers_autenticado)
    assert r.status_code in (400, 403, 404)


def test_eliminar_categoria_inexistente_falha(client, headers_autenticado):
    r = client.delete("/categorias/999999", headers=headers_autenticado)
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "CATEGORIA_NAO_ENCONTRADA"


def test_editar_categoria_para_grupo_destino_inexistente_falha(client, headers_autenticado):
    tech = grupo(client, headers_autenticado, "Tecnologia")
    software = next(c for c in tech["categorias"] if c["nome"] == "Software")

    r = client.put(f"/categorias/{software['id']}", json={"nome": "Software", "parent_id": 999999}, headers=headers_autenticado)
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "GRUPO_DESTINO_NAO_ENCONTRADO"


def test_eliminar_categoria_com_destino_de_tipo_incompativel_falha(client, headers_autenticado):
    """migrar_para_id aponta para um grupo, não uma categoria-folha — tipos incompatíveis,
    mesmo sendo ambos de saída."""
    tech = grupo(client, headers_autenticado, "Tecnologia")
    hardware = next(c for c in tech["categorias"] if c["nome"] == "Hardware")
    entretenimento = grupo(client, headers_autenticado, "Entretenimento")

    r = client.delete(f"/categorias/{hardware['id']}?migrar_para_id={entretenimento['id']}", headers=headers_autenticado)
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "DESTINO_TIPO_INCOMPATIVEL"


def test_eliminar_categoria_com_destino_de_direcao_incompativel_falha(client, headers_autenticado):
    """migrar_para_id é uma categoria-folha válida, mas de direcção oposta (entrada vs
    saída)."""
    tech = grupo(client, headers_autenticado, "Tecnologia")
    hardware = next(c for c in tech["categorias"] if c["nome"] == "Hardware")
    trabalho = grupo(client, headers_autenticado, "Trabalho")
    salario = next(c for c in trabalho["categorias"] if c["nome"] == "Salário")

    r = client.delete(f"/categorias/{hardware['id']}?migrar_para_id={salario['id']}", headers=headers_autenticado)
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "DESTINO_DIRECAO_INCOMPATIVEL"


# ═══════════════════════════════════════════════════════════
# DELETE /categorias/{id} — grupo
# ═══════════════════════════════════════════════════════════
def test_eliminar_grupo_sem_subcategorias(client, headers_autenticado):
    client.post("/categorias", json={"nome": "Grupo Vazio", "eh_recebimento": False}, headers=headers_autenticado)
    vazio = grupo(client, headers_autenticado, "Grupo Vazio")
    r = client.delete(f"/categorias/{vazio['id']}", headers=headers_autenticado)
    assert r.status_code == 200


def test_eliminar_grupo_com_subcategorias_pede_confirmacao(client, headers_autenticado):
    tech = grupo(client, headers_autenticado, "Tecnologia")
    r = client.delete(f"/categorias/{tech['id']}", headers=headers_autenticado)
    assert r.status_code == 400
    detail = r.json()["detail"]
    assert detail["code"] == "GRUPO_COM_CATEGORIAS"
    # ctx em bruto (não só a mensagem já em português) — ver
    # static/js/i18n.js::ERROS_TRADUCOES.en.GRUPO_COM_CATEGORIAS.
    assert detail["ctx"] == {"n": len(tech["categorias"])}


def test_eliminar_grupo_com_migracao_move_subcategorias(client, headers_autenticado):
    tech = grupo(client, headers_autenticado, "Tecnologia")
    ent  = grupo(client, headers_autenticado, "Entretenimento")

    r = client.delete(f"/categorias/{tech['id']}?migrar_para_id={ent['id']}", headers=headers_autenticado)
    assert r.status_code == 200

    ent2 = grupo(client, headers_autenticado, "Entretenimento")
    assert any(c["nome"] == "Hardware" for c in ent2["categorias"])
    assert not any(g["nome"] == "Tecnologia" for g in arvore(client, headers_autenticado))


def test_eliminar_grupo_com_forcar_remove_tudo(client, headers_autenticado, conta_id):
    tech = grupo(client, headers_autenticado, "Tecnologia")
    hardware = next(c for c in tech["categorias"] if c["nome"] == "Hardware")
    client.post("/movimentos", json={
        "conta_id": conta_id, "data": hoje(), "descricao": "Teclado",
        "valor": -50.0, "categoria_id": hardware["id"],
    }, headers=headers_autenticado)

    r = client.delete(f"/categorias/{tech['id']}?forcar=true", headers=headers_autenticado)
    assert r.status_code == 200
    assert client.get("/movimentos", headers=headers_autenticado).json() == []
    assert not any(g["nome"] == "Tecnologia" for g in arvore(client, headers_autenticado))


def test_nao_e_possivel_eliminar_a_folha_outros_protegida(client, headers_autenticado):
    outros_pagamentos = grupo(client, headers_autenticado, "Outros Pagamentos")
    outros = next(c for c in outros_pagamentos["categorias"] if c["nome"] == "Outros")
    r = client.delete(f"/categorias/{outros['id']}", headers=headers_autenticado)
    assert r.status_code == 400


def test_nao_e_possivel_renomear_a_folha_outros_protegida(client, headers_autenticado):
    outros_pagamentos = grupo(client, headers_autenticado, "Outros Pagamentos")
    outros = next(c for c in outros_pagamentos["categorias"] if c["nome"] == "Outros")
    r = client.put(f"/categorias/{outros['id']}", json={"nome": "Diversos"}, headers=headers_autenticado)
    assert r.status_code == 400


def test_e_possivel_renomear_o_grupo_outros_pagamentos(client, headers_autenticado):
    outros_pagamentos = grupo(client, headers_autenticado, "Outros Pagamentos")
    r = client.put(f"/categorias/{outros_pagamentos['id']}", json={"nome": "Diversos"}, headers=headers_autenticado)
    assert r.status_code == 200


def test_e_possivel_adicionar_categoria_nova_a_outros_pagamentos(client, headers_autenticado):
    outros_pagamentos = grupo(client, headers_autenticado, "Outros Pagamentos")
    r = client.post("/categorias", json={"nome": "Multas", "parent_id": outros_pagamentos["id"]}, headers=headers_autenticado)
    assert r.status_code == 200


def test_nao_e_possivel_forcar_eliminacao_do_grupo_outros_pagamentos(client, headers_autenticado):
    outros_pagamentos = grupo(client, headers_autenticado, "Outros Pagamentos")
    r = client.delete(f"/categorias/{outros_pagamentos['id']}?forcar=true", headers=headers_autenticado)
    assert r.status_code == 400


def test_categoria_outros_aparece_normalmente_em_categorias_flat(client, headers_autenticado):
    categorias = client.get("/categorias", headers=headers_autenticado).json()
    assert any(c["nome"] == "Outros" and c["grupo"] == "Outros Pagamentos" for c in categorias)

def test_nao_e_possivel_eliminar_grupo_outros_pagamentos_mesmo_com_migracao(client, headers_autenticado):
    outros_pagamentos = grupo(client, headers_autenticado, "Outros Pagamentos")
    habitacao = grupo(client, headers_autenticado, "Habitação")

    r = client.delete(f"/categorias/{outros_pagamentos['id']}?migrar_para_id={habitacao['id']}", headers=headers_autenticado)
    assert r.status_code == 400


# ═══════════════════════════════════════════════════════════
# Validação de campos
# ═══════════════════════════════════════════════════════════
def test_criar_categoria_com_nome_vazio_falha(client, headers_autenticado):
    r = client.post("/categorias", json={"nome": "", "eh_recebimento": True}, headers=headers_autenticado)
    assert r.status_code == 422


def test_criar_categoria_com_nome_demasiado_longo_falha(client, headers_autenticado):
    r = client.post("/categorias", json={"nome": "x" * 81, "eh_recebimento": True}, headers=headers_autenticado)
    assert r.status_code == 422