from datetime import date
from app.db.database import get_connection

def hoje():
    return str(date.today())


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


def test_arvore_tem_grupos_padrao_com_subcategorias(client, headers_autenticado):
    a = arvore(client, headers_autenticado)
    assert any(g["nome"] == "Trabalho" for g in a)
    trabalho = grupo(client, headers_autenticado, "Trabalho")
    assert any(c["nome"] == "Salário" for c in trabalho["categorias"])


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


# ═══════════════════════════════════════════════════════════
# DELETE /categorias/{id} — categoria folha
# ═══════════════════════════════════════════════════════════
def test_eliminar_categoria_folha_sem_movimentos(client, headers_autenticado):
    tech = grupo(client, headers_autenticado, "Tecnologia")
    outros = next(c for c in tech["categorias"] if c["nome"] == "Outros")
    r = client.delete(f"/categorias/{outros['id']}", headers=headers_autenticado)
    assert r.status_code == 200


def test_eliminar_categoria_folha_com_movimentos_pede_confirmacao(client, headers_autenticado, conta_id):
    tech = grupo(client, headers_autenticado, "Tecnologia")
    hardware = next(c for c in tech["categorias"] if c["nome"] == "Hardware")
    client.post("/movimentos", json={
        "conta_id": conta_id, "data": hoje(), "descricao": "Teclado",
        "valor": -50.0, "categoria_id": hardware["id"],
    }, headers=headers_autenticado)

    r = client.delete(f"/categorias/{hardware['id']}", headers=headers_autenticado)
    assert r.status_code == 400


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


# ═══════════════════════════════════════════════════════════
# POST /categorias/{id}/mover
# ═══════════════════════════════════════════════════════════
def test_mover_categoria_dentro_do_grupo(client, headers_autenticado):
    tech = grupo(client, headers_autenticado, "Tecnologia")
    primeira, segunda = tech["categorias"][0], tech["categorias"][1]

    r = client.post(f"/categorias/{primeira['id']}/mover?direcao=down", headers=headers_autenticado)
    assert r.status_code == 200
    tech2 = grupo(client, headers_autenticado, "Tecnologia")
    assert tech2["categorias"][0]["nome"] == segunda["nome"]


def test_mover_primeira_categoria_para_cima_nao_faz_nada(client, headers_autenticado):
    tech = grupo(client, headers_autenticado, "Tecnologia")
    primeira = tech["categorias"][0]

    r = client.post(f"/categorias/{primeira['id']}/mover?direcao=up", headers=headers_autenticado)
    assert r.status_code == 200
    tech2 = grupo(client, headers_autenticado, "Tecnologia")
    assert tech2["categorias"][0]["nome"] == primeira["nome"]


def test_mover_grupo_de_topo(client, headers_autenticado):
    despesas = [g for g in arvore(client, headers_autenticado) if not g["eh_recebimento"]]
    primeiro, segundo = despesas[0], despesas[1]

    r = client.post(f"/categorias/{primeiro['id']}/mover?direcao=down", headers=headers_autenticado)
    assert r.status_code == 200
    despesas2 = [g for g in arvore(client, headers_autenticado) if not g["eh_recebimento"]]
    assert despesas2[0]["nome"] == segundo["nome"]

# ---
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