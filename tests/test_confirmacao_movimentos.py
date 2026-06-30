from app.db.database import get_connection, release_connection, release_connection
from tests.helpers import criar_movimento


def forcar_origem(movimento_id, origem):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE movimentos SET origem_cat=%s WHERE id=%s", (origem, movimento_id))
    conn.commit()
    cursor.close()
    release_connection(conn)


# ═══════════════════════════════════════════════════════════
# GET /movimentos?precisa_confirmacao=
# ═══════════════════════════════════════════════════════════
def test_movimento_manual_nao_aparece_como_pendente(client, headers_autenticado, conta_id, categoria_id):
    criar_movimento(client, headers_autenticado, conta_id, categoria_id)
    r = client.get("/movimentos?precisa_confirmacao=true", headers=headers_autenticado).json()
    assert r == []


def test_movimento_llm_aparece_como_pendente(client, headers_autenticado, conta_id, categoria_id):
    mid = criar_movimento(client, headers_autenticado, conta_id, categoria_id)
    forcar_origem(mid, "llm")
    r = client.get("/movimentos?precisa_confirmacao=true", headers=headers_autenticado).json()
    assert len(r) == 1
    assert r[0]["id"] == mid


def test_movimento_sem_match_aparece_como_pendente(client, headers_autenticado, conta_id, categoria_id):
    mid = criar_movimento(client, headers_autenticado, conta_id, categoria_id)
    forcar_origem(mid, "sem_match")
    r = client.get("/movimentos?precisa_confirmacao=true", headers=headers_autenticado).json()
    assert len(r) == 1


def test_movimento_regra_nao_aparece_como_pendente(client, headers_autenticado, conta_id, categoria_id):
    mid = criar_movimento(client, headers_autenticado, conta_id, categoria_id)
    forcar_origem(mid, "regra")
    r = client.get("/movimentos?precisa_confirmacao=true", headers=headers_autenticado).json()
    assert r == []


def test_movimento_cache_nao_aparece_como_pendente(client, headers_autenticado, conta_id, categoria_id):
    mid = criar_movimento(client, headers_autenticado, conta_id, categoria_id)
    forcar_origem(mid, "cache")
    r = client.get("/movimentos?precisa_confirmacao=true", headers=headers_autenticado).json()
    assert r == []


def test_filtro_precisa_confirmacao_false_exclui_pendentes(client, headers_autenticado, conta_id, categoria_id):
    mid_manual = criar_movimento(client, headers_autenticado, conta_id, categoria_id, descricao="Manual")
    mid_llm = criar_movimento(client, headers_autenticado, conta_id, categoria_id, descricao="Auto")
    forcar_origem(mid_llm, "llm")

    r = client.get("/movimentos?precisa_confirmacao=false", headers=headers_autenticado).json()
    assert len(r) == 1
    assert r[0]["id"] == mid_manual


# ═══════════════════════════════════════════════════════════
# GET /movimentos/pendentes/contagem
# ═══════════════════════════════════════════════════════════
def test_contagem_pendentes_comeca_em_zero(client, headers_autenticado):
    r = client.get("/movimentos/pendentes/contagem", headers=headers_autenticado).json()
    assert r["contagem"] == 0


def test_contagem_pendentes_reflete_movimentos_automaticos(client, headers_autenticado, conta_id, categoria_id):
    mid1 = criar_movimento(client, headers_autenticado, conta_id, categoria_id, descricao="A")
    mid2 = criar_movimento(client, headers_autenticado, conta_id, categoria_id, descricao="B")
    forcar_origem(mid1, "llm")
    forcar_origem(mid2, "sem_match")

    r = client.get("/movimentos/pendentes/contagem", headers=headers_autenticado).json()
    assert r["contagem"] == 2


def test_contagem_pendentes_e_isolada_por_utilizador(client, headers_autenticado, conta_id, categoria_id):
    mid = criar_movimento(client, headers_autenticado, conta_id, categoria_id)
    forcar_origem(mid, "llm")

    client.post("/registro", json={"nome": "Outro", "email": "outro@exemplo.com", "password": "senha123"})
    r_outro = client.post("/login", json={"email": "outro@exemplo.com", "password": "senha123"})
    headers_outro = {"Authorization": f"Bearer {r_outro.json()['token']}"}

    r = client.get("/movimentos/pendentes/contagem", headers=headers_outro).json()
    assert r["contagem"] == 0


# ═══════════════════════════════════════════════════════════
# POST /movimentos/{id}/confirmar
# ═══════════════════════════════════════════════════════════
def test_confirmar_movimento_marca_como_manual(client, headers_autenticado, conta_id, categoria_id):
    mid = criar_movimento(client, headers_autenticado, conta_id, categoria_id)
    forcar_origem(mid, "llm")

    r = client.post(f"/movimentos/{mid}/confirmar", headers=headers_autenticado)
    assert r.status_code == 200

    movimento = client.get("/movimentos", headers=headers_autenticado).json()[0]
    assert movimento["origem_cat"] == "manual"


def test_confirmar_movimento_sai_da_lista_de_pendentes(client, headers_autenticado, conta_id, categoria_id):
    mid = criar_movimento(client, headers_autenticado, conta_id, categoria_id)
    forcar_origem(mid, "llm")
    client.post(f"/movimentos/{mid}/confirmar", headers=headers_autenticado)

    r = client.get("/movimentos?precisa_confirmacao=true", headers=headers_autenticado).json()
    assert r == []


def test_confirmar_movimento_inexistente_falha(client, headers_autenticado):
    r = client.post("/movimentos/id-inexistente/confirmar", headers=headers_autenticado)
    assert r.status_code == 404


def test_confirmar_movimento_de_outro_utilizador_falha(client, headers_autenticado, conta_id, categoria_id):
    mid = criar_movimento(client, headers_autenticado, conta_id, categoria_id)
    forcar_origem(mid, "llm")

    client.post("/registro", json={"nome": "Outro", "email": "outro@exemplo.com", "password": "senha123"})
    r_outro = client.post("/login", json={"email": "outro@exemplo.com", "password": "senha123"})
    headers_outro = {"Authorization": f"Bearer {r_outro.json()['token']}"}

    r = client.post(f"/movimentos/{mid}/confirmar", headers=headers_outro)
    assert r.status_code == 404


def test_confirmar_movimento_alimenta_o_cache_de_categorizacao(client, headers_autenticado, conta_id, categoria_id):
    mid = criar_movimento(client, headers_autenticado, conta_id, categoria_id, descricao="LOJA NOVA LDA")
    forcar_origem(mid, "llm")
    client.post(f"/movimentos/{mid}/confirmar", headers=headers_autenticado)

    from app.services.categorizacao import buscar_em_cache
    uid = client.get("/me", headers=headers_autenticado).json()["id"]
    conn = get_connection()
    categoria_em_cache = buscar_em_cache(conn, "LOJA NOVA LDA", uid, False)
    release_connection(conn)
    assert categoria_em_cache == (categoria_id, True)


# ═══════════════════════════════════════════════════════════
# POST /movimentos/confirmar-todos
# ═══════════════════════════════════════════════════════════
def test_confirmar_todos_marca_apenas_os_pendentes(client, headers_autenticado, conta_id, categoria_id):
    criar_movimento(client, headers_autenticado, conta_id, categoria_id, descricao="Manual")
    mid_llm = criar_movimento(client, headers_autenticado, conta_id, categoria_id, descricao="Auto1")
    mid_sem = criar_movimento(client, headers_autenticado, conta_id, categoria_id, descricao="Auto2")
    forcar_origem(mid_llm, "llm")
    forcar_origem(mid_sem, "sem_match")

    r = client.post("/movimentos/confirmar-todos", headers=headers_autenticado)
    assert r.status_code == 200
    assert r.json()["confirmados"] == 2

    pendentes = client.get("/movimentos?precisa_confirmacao=true", headers=headers_autenticado).json()
    assert pendentes == []


def test_confirmar_todos_sem_pendentes_nao_falha(client, headers_autenticado):
    r = client.post("/movimentos/confirmar-todos", headers=headers_autenticado)
    assert r.status_code == 200
    assert r.json()["confirmados"] == 0


def test_confirmar_todos_e_isolado_por_utilizador(client, headers_autenticado, conta_id, categoria_id):
    mid = criar_movimento(client, headers_autenticado, conta_id, categoria_id)
    forcar_origem(mid, "llm")

    client.post("/registro", json={"nome": "Outro", "email": "outro@exemplo.com", "password": "senha123"})
    r_outro = client.post("/login", json={"email": "outro@exemplo.com", "password": "senha123"})
    headers_outro = {"Authorization": f"Bearer {r_outro.json()['token']}"}

    client.post("/movimentos/confirmar-todos", headers=headers_outro)

    pendentes_ana = client.get("/movimentos?precisa_confirmacao=true", headers=headers_autenticado).json()
    assert len(pendentes_ana) == 1