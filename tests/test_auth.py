import pytest
from psycopg2.extras import RealDictCursor

from app.core.dominio import ErroDominio
from app.db.database import get_connection, release_connection
from app.schemas.auth import RegistoInput
from app.services import auth as servico_auth


def test_registo_com_sucesso(client):
    r = client.post("/registro", json={
        "nome": "Ana", "email": "ana@exemplo.com", "password": "senha123"
    })
    assert r.status_code == 200
    dados = r.json()
    assert "token" in dados
    assert dados["nome"] == "Ana"


def test_registo_email_duplicado(client):
    client.post("/registro", json={"nome": "Ana", "email": "ana@exemplo.com", "password": "senha123"})
    r = client.post("/registro", json={"nome": "Outra", "email": "ana@exemplo.com", "password": "outra123"})
    assert r.status_code == 400


def test_registo_email_duplicado_e_insensivel_a_maiusculas(client):
    client.post("/registro", json={"nome": "Ana", "email": "ana@exemplo.com", "password": "senha123"})
    r = client.post("/registro", json={"nome": "Outra", "email": "Ana@Exemplo.com", "password": "outra123"})
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "EMAIL_JA_REGISTADO"


def test_login_e_insensivel_a_maiusculas_no_email(client):
    client.post("/registro", json={"nome": "Ana", "email": "ana@exemplo.com", "password": "senha123"})
    r = client.post("/login", json={"email": "Ana@Exemplo.com", "password": "senha123"})
    assert r.status_code == 200


def test_login_com_sucesso(client):
    client.post("/registro", json={"nome": "Ana", "email": "ana@exemplo.com", "password": "senha123"})
    r = client.post("/login", json={"email": "ana@exemplo.com", "password": "senha123"})
    assert r.status_code == 200
    assert "token" in r.json()


def test_login_password_errada(client):
    client.post("/registro", json={"nome": "Ana", "email": "ana@exemplo.com", "password": "senha123"})
    r = client.post("/login", json={"email": "ana@exemplo.com", "password": "errada"})
    assert r.status_code == 401


def test_me_sem_token_falha(client):
    r = client.get("/me")
    assert r.status_code == 401


def test_me_com_token_devolve_dados_corretos(client, headers_autenticado):
    r = client.get("/me", headers=headers_autenticado)
    assert r.status_code == 200
    assert r.json()["nome"] == "Ana"
    assert r.json()["email"] == "ana@exemplo.com"


# ═══════════════════════════════════════════════════════════
# RATE LIMITING
# ═══════════════════════════════════════════════════════════
def test_limite_de_registos_por_minuto(client):
    for i in range(5):
        r = client.post("/registro", json={
            "nome": f"User {i}", "email": f"user{i}@exemplo.com", "password": "senha123"
        })
        assert r.status_code == 200

    r6 = client.post("/registro", json={
        "nome": "User 6", "email": "user6@exemplo.com", "password": "senha123"
    })
    assert r6.status_code == 429


def test_limite_de_logins_por_minuto(client, headers_autenticado):
    for _ in range(5):
        r = client.post("/login", json={"email": "ana@exemplo.com", "password": "senha123"})
        assert r.status_code == 200

    r6 = client.post("/login", json={"email": "ana@exemplo.com", "password": "senha123"})
    assert r6.status_code == 429

# ---
def test_registo_com_email_invalido_deveria_falhar(client):
    r = client.post("/registro", json={
        "nome": "Mal Formado", "email": "isto-nao-e-um-email", "password": "senha123"
    })
    assert r.status_code == 422


def test_registo_com_password_curta_falha(client):
    r = client.post("/registro", json={"nome": "X", "email": "x@exemplo.com", "password": "123"})
    assert r.status_code == 422


def test_registo_com_falha_no_seed_nao_deixa_conta_orfa(client, monkeypatch):
    """Se o seed de categorias falhar a meio, a conta não pode ficar criada sem
    categorias e com o email já ocupado para sempre — a transacção inteira tem de
    reverter (ver services/auth.py::criar_utilizador)."""
    def seed_falha(cursor, utilizador_id):
        raise RuntimeError("falha propositada a meio do seed")

    monkeypatch.setattr("app.services.auth.seed_categorias_padrao", seed_falha)

    with pytest.raises(RuntimeError):
        client.post("/registro", json={"nome": "Ana", "email": "ana@exemplo.com", "password": "senha123"})

    monkeypatch.undo()

    r = client.post("/registro", json={"nome": "Ana", "email": "ana@exemplo.com", "password": "senha123"})
    assert r.status_code == 200, "o email devia estar livre — o registo anterior tem de ter revertido por completo"


def test_registo_com_nome_vazio_falha(client):
    r = client.post("/registro", json={"nome": "", "email": "x@exemplo.com", "password": "senha123"})
    assert r.status_code == 422


class _CursorSemDeteccaoDaCorrida:
    """Envolve um cursor real, mas finge que a verificação SELECT inicial de
    criar_utilizador (\"este email já existe?\") não encontrou nada — simula a corrida rara
    em que dois registos com o mesmo email passam essa verificação ao mesmo tempo; só o
    UNIQUE constraint do INSERT a seguir é que apanha de facto."""
    def __init__(self, cursor):
        self._cursor = cursor
        self._ja_respondeu = False

    def execute(self, *args, **kwargs):
        return self._cursor.execute(*args, **kwargs)

    def fetchone(self):
        if not self._ja_respondeu:
            self._ja_respondeu = True
            return None
        return self._cursor.fetchone()


def test_criar_utilizador_com_corrida_no_insert_da_erro_amigavel():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute(
            "INSERT INTO utilizadores (nome, email, password) VALUES (%s, %s, %s)",
            ("Já Registado", "corrida@exemplo.com", "hash-qualquer"),
        )
        dados = RegistoInput(nome="Novo", email="corrida@exemplo.com", password="senha12345")

        with pytest.raises(ErroDominio) as exc:
            servico_auth.criar_utilizador(_CursorSemDeteccaoDaCorrida(cursor), conn, dados)
        assert exc.value.code == "EMAIL_JA_REGISTADO"
    finally:
        conn.rollback()
        cursor.close()
        release_connection(conn)


def test_registo_com_varios_campos_invalidos_expoe_todos_os_erros(client):
    r = client.post("/registro", json={"nome": "", "email": "nao-e-email", "password": "123"})
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert len(detail["errors"]) == 3
    campos = {e["campo"] for e in detail["errors"]}
    assert campos == {"nome", "email", "password"}
    # o topo continua a ser o primeiro erro, para quem só lê code/message (ex. frontend)
    assert detail["code"] == detail["errors"][0]["code"]


def test_erro_de_password_curta_expoe_ctx_com_min_length(client):
    """ctx em bruto (ex. min_length) é o que permite a um cliente formatar a sua própria
    mensagem (ex. em inglês) sem depender do texto português de "message"."""
    r = client.post("/registro", json={"nome": "X", "email": "x@exemplo.com", "password": "123"})
    assert r.status_code == 422
    erro_password = next(e for e in r.json()["detail"]["errors"] if e["campo"] == "password")
    assert erro_password["code"] == "STRING_TOO_SHORT"
    assert erro_password["ctx"] == {"min_length": 8}