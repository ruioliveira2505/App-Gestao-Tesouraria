"""Endpoints de sistema (`app/main.py`, tag "sistema") — ping simples e health check para
deploy. Nenhum dos dois tinha teste algum antes desta ronda de cobertura."""


def test_raiz_devolve_status_ok(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "projeto": "tesouraria"}


def test_health_devolve_ok_com_bd_disponivel(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "database": "ok"}


def test_health_devolve_degradado_se_bd_indisponivel(client, monkeypatch):
    def get_connection_que_falha():
        raise RuntimeError("BD propositadamente em baixo")

    monkeypatch.setattr("app.main.get_connection", get_connection_que_falha)

    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "degraded", "database": "unreachable"}
