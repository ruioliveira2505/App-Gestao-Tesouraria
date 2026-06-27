from app.db.database import get_connection
from tests.helpers import hoje


# ═══════════════════════════════════════════════════════════
# PUT /me — atualizar perfil
# ═══════════════════════════════════════════════════════════
def test_atualizar_perfil_com_sucesso(client, headers_autenticado):
    r = client.put("/me", json={
        "nome": "Ana Maria", "email": "ana.maria@exemplo.com"
    }, headers=headers_autenticado)
    assert r.status_code == 200
    assert r.json()["nome"] == "Ana Maria"

    dados = client.get("/me", headers=headers_autenticado).json()
    assert dados["nome"] == "Ana Maria"
    assert dados["email"] == "ana.maria@exemplo.com"


def test_atualizar_perfil_sem_token_falha(client):
    r = client.put("/me", json={"nome": "X", "email": "x@exemplo.com"})
    assert r.status_code == 401


def test_login_com_novo_email_funciona_apos_atualizar(client, headers_autenticado):
    client.put("/me", json={
        "nome": "Ana", "email": "novo@exemplo.com"
    }, headers=headers_autenticado)

    r = client.post("/login", json={"email": "novo@exemplo.com", "password": "senha123"})
    assert r.status_code == 200


def test_login_com_email_antigo_falha_apos_atualizar(client, headers_autenticado):
    client.put("/me", json={
        "nome": "Ana", "email": "novo2@exemplo.com"
    }, headers=headers_autenticado)

    r = client.post("/login", json={"email": "ana@exemplo.com", "password": "senha123"})
    assert r.status_code == 401


def test_atualizar_email_para_email_ja_existente_falha_graciosamente(client, headers_autenticado):
    client.post("/registro", json={
        "nome": "Outro", "email": "outro@exemplo.com", "password": "senha123"
    })

    r = client.put("/me", json={
        "nome": "Ana", "email": "outro@exemplo.com"
    }, headers=headers_autenticado)
    assert r.status_code == 400


# ═══════════════════════════════════════════════════════════
# PUT /me/password
# ═══════════════════════════════════════════════════════════
def test_atualizar_password_com_sucesso(client, headers_autenticado):
    r = client.put("/me/password", json={
        "password_atual": "senha123", "password_nova": "nova45678"
    }, headers=headers_autenticado)
    assert r.status_code == 200

    r_velha = client.post("/login", json={"email": "ana@exemplo.com", "password": "senha123"})
    assert r_velha.status_code == 401

    r_nova = client.post("/login", json={"email": "ana@exemplo.com", "password": "nova45678"})
    assert r_nova.status_code == 200


def test_atualizar_password_atual_incorreta_falha(client, headers_autenticado):
    r = client.put("/me/password", json={
        "password_atual": "errada", "password_nova": "nova45678"
    }, headers=headers_autenticado)
    assert r.status_code == 401

    r_login = client.post("/login", json={"email": "ana@exemplo.com", "password": "senha123"})
    assert r_login.status_code == 200


def test_atualizar_password_sem_token_falha(client):
    r = client.put("/me/password", json={"password_atual": "a", "password_nova": "b"})
    assert r.status_code == 401


# ═══════════════════════════════════════════════════════════
# DELETE /me — eliminação total da conta
# ═══════════════════════════════════════════════════════════
def test_eliminar_conta_sem_token_falha(client):
    r = client.delete("/me")
    assert r.status_code == 401


def test_eliminar_conta_utilizador_remove_tudo_em_cascata(client, headers_autenticado, conta_id, categoria_id):
    uid = client.get("/me", headers=headers_autenticado).json()["id"]

    r = client.post("/movimentos", json={
        "conta_id": conta_id, "data": hoje(), "descricao": "Antes de eliminar",
        "valor": -10.0, "categoria_id": categoria_id,
    }, headers=headers_autenticado)
    movimento_id = client.get("/movimentos", headers=headers_autenticado).json()[0]["id"]

    # provoca escrita em categorias_aprendidas (só acontece no editar, não no criar)
    client.put(f"/movimentos/{movimento_id}", json={
        "conta_id": conta_id, "data": hoje(), "descricao": "Antes de eliminar",
        "valor": -10.0, "categoria_id": categoria_id,
    }, headers=headers_autenticado)

    r = client.delete("/me", headers=headers_autenticado)
    assert r.status_code == 200

    conn = get_connection()
    cursor = conn.cursor()
    for tabela in ["movimentos", "categorias", "contas", "categorias_aprendidas"]:
        cursor.execute(f"SELECT COUNT(*) FROM {tabela} WHERE utilizador_id = %s", (uid,))
        assert cursor.fetchone()[0] == 0, f"{tabela} ainda tem linhas do utilizador eliminado"

    cursor.execute("SELECT COUNT(*) FROM utilizadores WHERE id = %s", (uid,))
    assert cursor.fetchone()[0] == 0

    cursor.execute("SELECT COUNT(*) FROM ajustes_saldo WHERE conta_id = %s", (conta_id,))
    assert cursor.fetchone()[0] == 0

    cursor.close()
    conn.close()


def test_login_falha_apos_eliminar_conta(client, headers_autenticado):
    client.delete("/me", headers=headers_autenticado)
    r = client.post("/login", json={"email": "ana@exemplo.com", "password": "senha123"})
    assert r.status_code == 401


def test_eliminar_conta_permite_reutilizar_o_email(client, headers_autenticado):
    client.delete("/me", headers=headers_autenticado)
    r = client.post("/registro", json={
        "nome": "Ana", "email": "ana@exemplo.com", "password": "outra789"
    })
    assert r.status_code == 200

# ---
def test_atualizar_perfil_com_email_invalido_deveria_falhar(client, headers_autenticado):
    r = client.put("/me", json={"nome": "Ana", "email": "nao-e-email"}, headers=headers_autenticado)
    assert r.status_code == 422


def test_atualizar_password_curta_falha(client, headers_autenticado):
    r = client.put("/me/password", json={
        "password_atual": "senha123", "password_nova": "abc"
    }, headers=headers_autenticado)
    assert r.status_code == 422