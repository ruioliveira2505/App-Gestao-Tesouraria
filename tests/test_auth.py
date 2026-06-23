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