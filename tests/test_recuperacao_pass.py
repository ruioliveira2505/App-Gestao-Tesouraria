import re
from datetime import timedelta
from app.core.security import criar_token


def extrair_token_do_corpo(corpo):
    match = re.search(r"token=(\S+)", corpo)
    return match.group(1) if match else None


# ═══════════════════════════════════════════════════════════
# POST /esqueci-password
# ═══════════════════════════════════════════════════════════
def test_esqueci_password_com_email_existente_envia_email(client, headers_autenticado, monkeypatch):
    enviados = []
    monkeypatch.setattr("app.routers.auth.enviar_email", lambda destinatario, assunto, corpo: enviados.append((destinatario, assunto, corpo)))

    r = client.post("/esqueci-password", json={"email": "ana@exemplo.com"})
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert len(enviados) == 1
    assert enviados[0][0] == "ana@exemplo.com"


def test_esqueci_password_com_email_inexistente_nao_revela_nem_envia(client, monkeypatch):
    enviados = []
    monkeypatch.setattr("app.routers.auth.enviar_email", lambda destinatario, assunto, corpo: enviados.append((destinatario, assunto, corpo)))

    r = client.post("/esqueci-password", json={"email": "naoexiste@exemplo.com"})
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert len(enviados) == 0


def test_esqueci_password_mensagem_identica_para_existente_e_inexistente(client, headers_autenticado, monkeypatch):
    monkeypatch.setattr("app.routers.auth.enviar_email", lambda *a, **k: None)

    r1 = client.post("/esqueci-password", json={"email": "ana@exemplo.com"})
    r2 = client.post("/esqueci-password", json={"email": "naoexiste@exemplo.com"})
    assert r1.json()["mensagem"] == r2.json()["mensagem"]


def test_limite_de_pedidos_esqueci_password(client, monkeypatch):
    monkeypatch.setattr("app.routers.auth.enviar_email", lambda *a, **k: None)

    for _ in range(3):
        r = client.post("/esqueci-password", json={"email": "qualquer@exemplo.com"})
        assert r.status_code == 200

    r4 = client.post("/esqueci-password", json={"email": "qualquer@exemplo.com"})
    assert r4.status_code == 429


# ═══════════════════════════════════════════════════════════
# POST /redefinir-password
# ═══════════════════════════════════════════════════════════
def test_redefinir_password_com_token_valido_funciona(client, headers_autenticado, monkeypatch):
    enviados = []
    monkeypatch.setattr("app.routers.auth.enviar_email", lambda destinatario, assunto, corpo: enviados.append(corpo))

    client.post("/esqueci-password", json={"email": "ana@exemplo.com"})
    token = extrair_token_do_corpo(enviados[0])
    assert token

    r = client.post("/redefinir-password", json={"token": token, "password_nova": "nova45678"})
    assert r.status_code == 200

    r_velha = client.post("/login", json={"email": "ana@exemplo.com", "password": "senha123"})
    assert r_velha.status_code == 401

    r_nova = client.post("/login", json={"email": "ana@exemplo.com", "password": "nova45678"})
    assert r_nova.status_code == 200


def test_redefinir_password_com_token_invalido_falha(client):
    r = client.post("/redefinir-password", json={"token": "isto-nao-e-um-jwt-valido", "password_nova": "nova45678"})
    assert r.status_code == 400


def test_redefinir_password_com_token_de_sessao_normal_falha(client, headers_autenticado):
    token_sessao = headers_autenticado["Authorization"].split(" ")[1]
    r = client.post("/redefinir-password", json={"token": token_sessao, "password_nova": "nova45678"})
    assert r.status_code == 400


def test_redefinir_password_com_token_expirado_falha(client, headers_autenticado):
    uid = client.get("/me", headers=headers_autenticado).json()["id"]
    token_expirado = criar_token({"sub": str(uid), "tipo": "reset"}, timedelta(seconds=-1))

    r = client.post("/redefinir-password", json={"token": token_expirado, "password_nova": "nova45678"})
    assert r.status_code == 400


def test_token_de_reset_nao_pode_acessar_rotas_normais(client, headers_autenticado, monkeypatch):
    enviados = []
    monkeypatch.setattr("app.routers.auth.enviar_email", lambda destinatario, assunto, corpo: enviados.append(corpo))
    client.post("/esqueci-password", json={"email": "ana@exemplo.com"})
    token_reset = extrair_token_do_corpo(enviados[0])

    r = client.get("/me", headers={"Authorization": f"Bearer {token_reset}"})
    assert r.status_code == 401


def test_redefinir_password_curta_falha(client, headers_autenticado, monkeypatch):
    enviados = []
    monkeypatch.setattr("app.routers.auth.enviar_email", lambda destinatario, assunto, corpo: enviados.append(corpo))
    client.post("/esqueci-password", json={"email": "ana@exemplo.com"})
    token = extrair_token_do_corpo(enviados[0])

    r = client.post("/redefinir-password", json={"token": token, "password_nova": "abc"})
    assert r.status_code == 422


def test_redefinir_password_com_token_ja_usado_falha(client, headers_autenticado, monkeypatch):
    enviados = []
    monkeypatch.setattr("app.routers.auth.enviar_email", lambda destinatario, assunto, corpo: enviados.append(corpo))
    client.post("/esqueci-password", json={"email": "ana@exemplo.com"})
    token = extrair_token_do_corpo(enviados[0])

    r1 = client.post("/redefinir-password", json={"token": token, "password_nova": "nova45678"})
    assert r1.status_code == 200

    r2 = client.post("/redefinir-password", json={"token": token, "password_nova": "outra999"})
    assert r2.status_code == 400


def test_redefinir_password_invalida_sessoes_anteriores(client, headers_autenticado, monkeypatch):
    enviados = []
    monkeypatch.setattr("app.routers.auth.enviar_email", lambda destinatario, assunto, corpo: enviados.append(corpo))
    client.post("/esqueci-password", json={"email": "ana@exemplo.com"})
    token_reset = extrair_token_do_corpo(enviados[0])

    r = client.post("/redefinir-password", json={"token": token_reset, "password_nova": "nova45678"})
    assert r.status_code == 200

    # o token de sessão que existia antes da redefinição deixa de ser válido
    assert client.get("/me", headers=headers_autenticado).status_code == 401