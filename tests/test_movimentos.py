import psycopg2
import pytest

from app.db.database import get_connection, release_connection
from tests.helpers import dias_atras, hoje, recuar_ancora


def movimento_exemplo(conta_id, categoria_id, **overrides):
    base = {
        "conta_id": conta_id, "data": hoje(), "descricao": "Compra teste",
        "valor": -50.0, "categoria_id": categoria_id,
    }
    base.update(overrides)
    return base


def test_listar_movimentos(client, headers_autenticado, conta_id, categoria_id):
    client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id), headers=headers_autenticado)
    r = client.get("/movimentos", headers=headers_autenticado)
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["descricao"] == "Compra teste"


def test_listar_movimentos_sem_limit_devolve_tudo(client, headers_autenticado, conta_id, categoria_id):
    for i in range(3):
        client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id, descricao=f"Mov {i}"), headers=headers_autenticado)
    r = client.get("/movimentos", headers=headers_autenticado)
    assert len(r.json()) == 3


def test_listar_movimentos_com_limit_e_offset_pagina_corretamente(client, headers_autenticado, conta_id, categoria_id):
    recuar_ancora(client, headers_autenticado, conta_id, dias_atras(5))
    for i in range(3):
        client.post("/movimentos", json=movimento_exemplo(
            conta_id, categoria_id, descricao=f"Mov {i}", data=dias_atras(2 - i)
        ), headers=headers_autenticado)

    pagina1 = client.get("/movimentos?limit=2&offset=0", headers=headers_autenticado).json()
    pagina2 = client.get("/movimentos?limit=2&offset=2", headers=headers_autenticado).json()

    assert len(pagina1) == 2
    assert len(pagina2) == 1
    # mais recente primeiro (ORDER BY data DESC) — "Mov 2" é o mais recente (dias_atras(0))
    assert pagina1[0]["descricao"] == "Mov 2"
    assert pagina2[0]["descricao"] == "Mov 0"


def test_filtrar_movimentos_por_conta(client, headers_autenticado, conta_id, categoria_id):
    client.post("/contas", json={
        "nome": "Outra Conta", "banco": "BPI", "tipo": "corrente",
        "iban": "PT50111111111111111111111", "moeda": "EUR", "saldo": 500.0,
        "data": hoje(),
    }, headers=headers_autenticado)
    outra_conta_id = next(c for c in client.get("/contas", headers=headers_autenticado).json() if c["nome"] == "Outra Conta")["id"]

    client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id, descricao="Da Principal"), headers=headers_autenticado)
    client.post("/movimentos", json=movimento_exemplo(outra_conta_id, categoria_id, descricao="Da Outra"), headers=headers_autenticado)

    r = client.get(f"/movimentos?conta_id={conta_id}", headers=headers_autenticado)
    movimentos = r.json()
    assert len(movimentos) == 1
    assert movimentos[0]["descricao"] == "Da Principal"


def test_filtrar_movimentos_por_direcao(client, headers_autenticado, conta_id, categoria_id):
    categorias = client.get("/categorias", headers=headers_autenticado).json()
    categoria_entrada_id = next(c for c in categorias if c["eh_recebimento"])["id"]

    client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id, descricao="Saída"), headers=headers_autenticado)
    client.post("/movimentos", json=movimento_exemplo(
        conta_id, categoria_entrada_id, descricao="Entrada", valor=200.0
    ), headers=headers_autenticado)

    r_in = client.get("/movimentos?direcao=in", headers=headers_autenticado)
    assert len(r_in.json()) == 1
    assert r_in.json()[0]["descricao"] == "Entrada"

    r_out = client.get("/movimentos?direcao=out", headers=headers_autenticado)
    assert len(r_out.json()) == 1
    assert r_out.json()[0]["descricao"] == "Saída"


def test_filtrar_movimentos_por_periodo(client, headers_autenticado, conta_id, categoria_id):
    recuar_ancora(client, headers_autenticado, conta_id, dias_atras(60))

    client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id, data=hoje(), descricao="Hoje"), headers=headers_autenticado)
    client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id, data=dias_atras(45), descricao="Antigo"), headers=headers_autenticado)

    r = client.get(f"/movimentos?data_de={dias_atras(50)}&data_ate={dias_atras(20)}", headers=headers_autenticado)
    movimentos = r.json()
    assert len(movimentos) == 1
    assert movimentos[0]["descricao"] == "Antigo"


def test_editar_movimento(client, headers_autenticado, conta_id, categoria_id):
    client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id), headers=headers_autenticado)
    movimento_id = client.get("/movimentos", headers=headers_autenticado).json()[0]["id"]

    r = client.put(f"/movimentos/{movimento_id}", json=movimento_exemplo(
        conta_id, categoria_id, descricao="Descrição Editada", valor=-75.0
    ), headers=headers_autenticado)
    assert r.status_code == 200

    movimentos = client.get("/movimentos", headers=headers_autenticado).json()
    assert movimentos[0]["descricao"] == "Descrição Editada"
    assert movimentos[0]["valor"] == -75.0


def test_eliminar_movimento(client, headers_autenticado, conta_id, categoria_id):
    client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id), headers=headers_autenticado)
    movimento_id = client.get("/movimentos", headers=headers_autenticado).json()[0]["id"]

    r = client.delete(f"/movimentos/{movimento_id}", headers=headers_autenticado)
    assert r.status_code == 200
    assert client.get("/movimentos", headers=headers_autenticado).json() == []


def test_movimento_afeta_saldo_atual_da_conta(client, headers_autenticado, conta_id, categoria_id):
    client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id, valor=-300.0), headers=headers_autenticado)

    contas = client.get("/contas", headers=headers_autenticado).json()
    assert contas[0]["saldo"] == 700.0  # 1000 - 300


def test_movimentos_de_outro_utilizador_nao_aparecem(client, headers_autenticado, conta_id, categoria_id):
    client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id), headers=headers_autenticado)

    client.post("/registro", json={"nome": "Outro", "email": "outro@exemplo.com", "password": "senha123"})
    r_outro = client.post("/login", json={"email": "outro@exemplo.com", "password": "senha123"})
    headers_outro = {"Authorization": f"Bearer {r_outro.json()['token']}"}

    r = client.get("/movimentos", headers=headers_outro)
    assert r.json() == []


def test_criar_movimento_antes_da_reconciliacao_falha(client, headers_autenticado, conta_id, categoria_id):
    r = client.post("/movimentos", json=movimento_exemplo(
        conta_id, categoria_id, data=dias_atras(10)
    ), headers=headers_autenticado)
    assert r.status_code == 400


def test_editar_movimento_para_data_antes_da_reconciliacao_falha(client, headers_autenticado, conta_id, categoria_id):
    client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id), headers=headers_autenticado)
    movimento_id = client.get("/movimentos", headers=headers_autenticado).json()[0]["id"]

    r = client.put(f"/movimentos/{movimento_id}", json=movimento_exemplo(
        conta_id, categoria_id, data=dias_atras(10)
    ), headers=headers_autenticado)
    assert r.status_code == 400


def test_criar_movimento_com_data_futura_falha(client, headers_autenticado, conta_id, categoria_id):
    r = client.post("/movimentos", json=movimento_exemplo(
        conta_id, categoria_id, data="2099-01-01"
    ), headers=headers_autenticado)
    assert r.status_code == 400


def test_editar_movimento_para_data_futura_falha(client, headers_autenticado, conta_id, categoria_id):
    client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id), headers=headers_autenticado)
    movimento_id = client.get("/movimentos", headers=headers_autenticado).json()[0]["id"]

    r = client.put(f"/movimentos/{movimento_id}", json=movimento_exemplo(
        conta_id, categoria_id, data="2099-01-01"
    ), headers=headers_autenticado)
    assert r.status_code == 400


def test_criar_movimento_com_categoria_da_direcao_errada_falha(client, headers_autenticado, conta_id):
    categorias = client.get("/categorias", headers=headers_autenticado).json()
    categoria_entrada = next(c for c in categorias if c["eh_recebimento"])

    r = client.post("/movimentos", json={
        "conta_id": conta_id, "data": hoje(), "descricao": "Errado",
        "valor": -50.0, "categoria_id": categoria_entrada["id"],
    }, headers=headers_autenticado)
    assert r.status_code == 400
    detail = r.json()["detail"]
    assert detail["code"] == "CATEGORIA_DIRECAO_ERRADA"
    # ctx em bruto (direcção do valor, não a palavra em português "Saída") — ver
    # static/js/i18n.js::ERROS_TRADUCOES.en.CATEGORIA_DIRECAO_ERRADA.
    assert detail["ctx"] == {"eh_recebimento": False}


def test_criar_movimento_antes_do_inicio_falha(client, headers_autenticado, conta_id, categoria_id):
    # a conta_id fixture tem âncora em "ontem" (ver conftest.py) — a Data de Início de
    # Movimentos é âncora+1 dia = hoje; um movimento datado da própria âncora é rejeitado.
    r = client.post("/movimentos", json={
        "conta_id": conta_id, "data": dias_atras(1), "descricao": "Muito cedo",
        "valor": -50.0, "categoria_id": categoria_id,
    }, headers=headers_autenticado)
    assert r.status_code == 400
    detail = r.json()["detail"]
    assert detail["code"] == "MOVIMENTO_ANTES_DO_INICIO"
    # ctx em bruto (data ISO, não o "dd-mm-aaaa" já formatado em português) — ver
    # static/js/i18n.js::ERROS_TRADUCOES.en.MOVIMENTO_ANTES_DO_INICIO.
    assert detail["ctx"] == {"data": hoje()}


def test_criar_movimento_com_categoria_inexistente_falha(client, headers_autenticado, conta_id):
    r = client.post("/movimentos", json=movimento_exemplo(conta_id, 999999), headers=headers_autenticado)
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "CATEGORIA_NAO_ENCONTRADA"


def test_criar_movimento_no_mesmo_dia_da_reconciliacao_mais_antiga_falha(client, headers_autenticado, conta_id, categoria_id):
    recuar_ancora(client, headers_autenticado, conta_id, hoje())  # âncora fica hoje

    r = client.post("/movimentos", json={
        "conta_id": conta_id, "data": hoje(), "descricao": "Teste",
        "valor": -10.0, "categoria_id": categoria_id,
    }, headers=headers_autenticado)
    assert r.status_code == 400


def test_criar_movimento_com_descricao_vazia_falha(client, headers_autenticado, conta_id, categoria_id):
    r = client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id, descricao=""), headers=headers_autenticado)
    assert r.status_code == 422


def test_criar_movimento_com_descricao_demasiado_longa_falha(client, headers_autenticado, conta_id, categoria_id):
    r = client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id, descricao="x" * 256), headers=headers_autenticado)
    assert r.status_code == 422


def test_origem_cat_fora_dos_valores_permitidos_e_rejeitado_pela_bd(client, headers_autenticado, conta_id, categoria_id):
    """Não há nenhum endpoint que deixe escolher origem_cat directamente — isto é uma
    rede de segurança ao nível da BD (migração 0011) contra um bug futuro que tente
    gravar um valor fora de 'manual'/'cache'/'llm'/'sem_match'."""
    client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id), headers=headers_autenticado)
    movimento_id = client.get("/movimentos", headers=headers_autenticado).json()[0]["id"]

    conn = get_connection()
    cursor = conn.cursor()
    try:
        with pytest.raises(psycopg2.errors.CheckViolation):
            cursor.execute("UPDATE movimentos SET origem_cat = 'valor_invalido' WHERE id = %s", (movimento_id,))
    finally:
        conn.rollback()
        cursor.close()
        release_connection(conn)


def test_criar_movimento_com_data_malformada_falha_com_422(client, headers_autenticado, conta_id, categoria_id):
    r = client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id, data="31-02-2026"), headers=headers_autenticado)
    assert r.status_code == 422


def test_falha_ao_gravar_cache_de_categorizacao_nao_impede_criacao_do_movimento(
    client, headers_autenticado, conta_id, categoria_id, monkeypatch,
):
    """_guardar_em_cache_seguro apanha qualquer excepção de guardar_em_cache — uma falha aí
    (ex. BD momentaneamente indisponível) não pode fazer o movimento, já gravado com
    sucesso, parecer que falhou."""
    def cache_que_falha(*args, **kwargs):
        raise RuntimeError("falha propositada — BD da cache indisponível")

    monkeypatch.setattr("app.services.movimentos.guardar_em_cache", cache_que_falha)

    r = client.post("/movimentos", json=movimento_exemplo(conta_id, categoria_id), headers=headers_autenticado)
    assert r.status_code == 200
    assert len(client.get("/movimentos", headers=headers_autenticado).json()) == 1