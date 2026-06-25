from app.services import categorizacao as nordigen
import requests
from app.db.database import get_connection


def uid_de(client, headers):
    return client.get("/me", headers=headers).json()["id"]


def id_categoria(client, headers, nome_grupo, nome_categoria):
    arvore = client.get("/categorias/arvore", headers=headers).json()
    grupo = next(g for g in arvore if g["nome"] == nome_grupo)
    return next(c["id"] for c in grupo["categorias"] if c["nome"] == nome_categoria)


# ═══════════════════════════════════════════════════════════
# resolver_categoria_id
# ═══════════════════════════════════════════════════════════
def test_resolver_categoria_id_encontra_categoria_existente(client, headers_autenticado):
    uid = uid_de(client, headers_autenticado)
    conn = get_connection()
    categoria_id = nordigen.resolver_categoria_id(conn, "Habitação", "Água, Eletricidade e Gás", uid)
    conn.close()

    esperado = id_categoria(client, headers_autenticado, "Habitação", "Água, Eletricidade e Gás")
    assert categoria_id == esperado


def test_resolver_categoria_id_devolve_none_se_nao_existir(client, headers_autenticado):
    uid = uid_de(client, headers_autenticado)
    conn = get_connection()
    categoria_id = nordigen.resolver_categoria_id(conn, "Grupo Inexistente", "Categoria Inexistente", uid)
    conn.close()
    assert categoria_id is None


def test_resolver_categoria_id_nao_atravessa_utilizadores(client, headers_autenticado):
    client.post("/registro", json={"nome": "Outro", "email": "outro@exemplo.com", "password": "senha123"})
    r_outro = client.post("/login", json={"email": "outro@exemplo.com", "password": "senha123"})
    uid_outro = client.get("/me", headers={"Authorization": f"Bearer {r_outro.json()['token']}"}).json()["id"]
    uid_ana = uid_de(client, headers_autenticado)

    conn = get_connection()
    categoria_id_ana   = nordigen.resolver_categoria_id(conn, "Habitação", "Água, Eletricidade e Gás", uid_ana)
    categoria_id_outro = nordigen.resolver_categoria_id(conn, "Habitação", "Água, Eletricidade e Gás", uid_outro)
    conn.close()

    assert categoria_id_ana is not None and categoria_id_outro is not None
    assert categoria_id_ana != categoria_id_outro


# ═══════════════════════════════════════════════════════════
# cache (categorias_aprendidas)
# ═══════════════════════════════════════════════════════════
def test_buscar_em_cache_sem_entrada_devolve_none(client, headers_autenticado):
    uid = uid_de(client, headers_autenticado)
    conn = get_connection()
    resultado = nordigen.buscar_em_cache(conn, "DESCRICAO NUNCA VISTA", uid)
    conn.close()
    assert resultado is None


def test_guardar_e_buscar_em_cache(client, headers_autenticado):
    uid = uid_de(client, headers_autenticado)
    categoria_id = id_categoria(client, headers_autenticado, "Tecnologia", "Hardware")

    conn = get_connection()
    nordigen.guardar_em_cache(conn, "LOJA GADGETS LDA", categoria_id, uid)
    resultado = nordigen.buscar_em_cache(conn, "LOJA GADGETS LDA", uid)
    conn.close()

    assert resultado == (categoria_id, False)   # não confirmado por defeito


def test_guardar_em_cache_atualiza_entrada_existente(client, headers_autenticado):
    uid = uid_de(client, headers_autenticado)
    hardware = id_categoria(client, headers_autenticado, "Tecnologia", "Hardware")
    software = id_categoria(client, headers_autenticado, "Tecnologia", "Software")

    conn = get_connection()
    nordigen.guardar_em_cache(conn, "LOJA GADGETS LDA", hardware, uid)
    nordigen.guardar_em_cache(conn, "LOJA GADGETS LDA", software, uid)
    resultado = nordigen.buscar_em_cache(conn, "LOJA GADGETS LDA", uid)
    conn.close()

    assert resultado == (software, False)


def test_cache_e_isolado_por_utilizador(client, headers_autenticado):
    client.post("/registro", json={"nome": "Outro", "email": "outro@exemplo.com", "password": "senha123"})
    r_outro = client.post("/login", json={"email": "outro@exemplo.com", "password": "senha123"})
    uid_outro = client.get("/me", headers={"Authorization": f"Bearer {r_outro.json()['token']}"}).json()["id"]
    uid_ana = uid_de(client, headers_autenticado)
    categoria_id = id_categoria(client, headers_autenticado, "Tecnologia", "Hardware")

    conn = get_connection()
    nordigen.guardar_em_cache(conn, "LOJA GADGETS LDA", categoria_id, uid_ana)
    resultado_outro = nordigen.buscar_em_cache(conn, "LOJA GADGETS LDA", uid_outro)
    conn.close()

    assert resultado_outro is None


# ═══════════════════════════════════════════════════════════
# categorizar() — orquestração: regras → cache → LLM → fallback
# ═══════════════════════════════════════════════════════════
def test_categorizar_usa_cache_confirmada_sem_chamar_llm(client, headers_autenticado, monkeypatch):
    uid = uid_de(client, headers_autenticado)
    categoria_id_esperada = id_categoria(client, headers_autenticado, "Tecnologia", "Hardware")

    conn = get_connection()
    nordigen.guardar_em_cache(conn, "LOJA GADGETS LDA", categoria_id_esperada, uid, confirmado=True)
    conn.close()

    chamou_llm = []
    monkeypatch.setattr(nordigen, "escolher_por_llm", lambda *a, **k: chamou_llm.append(1))

    categoria_id, origem = nordigen.categorizar("LOJA GADGETS LDA", -80.0, uid)

    assert origem == "cache"
    assert categoria_id == categoria_id_esperada
    assert chamou_llm == []


def test_categorizar_usa_cache_nao_confirmada_mas_continua_pendente(client, headers_autenticado, monkeypatch):
    """Uma sugestão do LLM ainda não confirmada deve continuar a aparecer como
    pendente ('llm'), mesmo já em cache — e sem voltar a gastar tokens."""
    uid = uid_de(client, headers_autenticado)
    categoria_id_esperada = id_categoria(client, headers_autenticado, "Tecnologia", "Hardware")

    conn = get_connection()
    nordigen.guardar_em_cache(conn, "LOJA GADGETS LDA", categoria_id_esperada, uid, confirmado=False)
    conn.close()

    chamou_llm = []
    monkeypatch.setattr(nordigen, "escolher_por_llm", lambda *a, **k: chamou_llm.append(1))

    categoria_id, origem = nordigen.categorizar("LOJA GADGETS LDA", -80.0, uid)

    assert origem == "llm"
    assert categoria_id == categoria_id_esperada
    assert chamou_llm == []


def test_categorizar_recorre_ao_llm_quando_nao_ha_regra_nem_cache(client, headers_autenticado, monkeypatch):
    uid = uid_de(client, headers_autenticado)
    categoria_id_llm = id_categoria(client, headers_autenticado, "Tecnologia", "Software")
    monkeypatch.setattr(nordigen, "escolher_por_llm", lambda descricao, valor, opcoes, contexto="": categoria_id_llm)

    categoria_id, origem = nordigen.categorizar("DESCRICAO MUITO ESTRANHA 123", -30.0, uid)

    assert origem == "llm"
    assert categoria_id == categoria_id_llm

    conn = get_connection()
    em_cache = nordigen.buscar_em_cache(conn, "DESCRICAO MUITO ESTRANHA 123", uid)
    conn.close()
    assert em_cache == (categoria_id_llm, False) # gravado, mas ainda não confirmado


def test_resolver_categoria_fallback_funciona_mesmo_com_nomes_repetidos(client, headers_autenticado):
    """Os dois grupos protegidos chamam-se ambos 'Sem Categoria' — confirma
    que a resolução por direção nunca devolve o da direção errada."""
    uid = uid_de(client, headers_autenticado)
    conn = get_connection()
    fallback_saida = nordigen.resolver_categoria_fallback(conn, False, uid)
    fallback_entrada = nordigen.resolver_categoria_fallback(conn, True, uid)
    conn.close()

    assert fallback_saida != fallback_entrada
    assert fallback_saida is not None and fallback_entrada is not None
    

def test_categorizar_com_conn_externa_nao_fecha_a_ligacao_do_chamador(client, headers_autenticado, monkeypatch):
    uid = uid_de(client, headers_autenticado)
    monkeypatch.setattr(nordigen, "escolher_por_llm", lambda *a, **k: None)

    conn = get_connection()
    nordigen.categorizar("QUALQUER COISA", -10.0, uid, conn=conn)

    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    assert cursor.fetchone() == (1,)  # se categorizar() tivesse fechado a ligação, isto falhava
    cursor.close()
    conn.close()


def test_categorizar_sem_conn_nao_deixa_ligacoes_penduradas(client, headers_autenticado, monkeypatch):
    uid = uid_de(client, headers_autenticado)
    monkeypatch.setattr(nordigen, "escolher_por_llm", lambda *a, **k: None)

    for _ in range(20):  # se cada chamada deixasse uma ligação aberta, isto esgotava o pool
        nordigen.categorizar("QUALQUER COISA", -10.0, uid)


def test_categorizar_por_llm_sem_categorias_disponiveis_devolve_none(client, headers_autenticado, monkeypatch):
    uid = uid_de(client, headers_autenticado)
    monkeypatch.setattr(nordigen, "listar_categorias_planas", lambda conn, uid, valor: [])
    chamou_llm = []
    monkeypatch.setattr(nordigen, "escolher_por_llm", lambda *a, **k: chamou_llm.append(1))

    conn = get_connection()
    resultado = nordigen.categorizar_por_llm("X", -10.0, conn, uid)
    conn.close()

    assert resultado is None
    assert chamou_llm == []


# ═══════════════════════════════════════════════════════════
# escolher_por_llm — chamada à API da Groq, isolada com mock de requests
# ═══════════════════════════════════════════════════════════
class RespostaFalsa:
    def __init__(self, texto, status_ok=True):
        self._texto = texto
        self._status_ok = status_ok

    def raise_for_status(self):
        if not self._status_ok:
            raise requests.HTTPError("erro simulado")

    def json(self):
        return {"choices": [{"message": {"content": self._texto}}]}


def test_escolher_por_llm_interpreta_resposta_numerica(monkeypatch):
    monkeypatch.setattr(nordigen, "GROQ_API_KEY", "chave-falsa-para-teste")
    opcoes = [(10, "Alimentação > Supermercado"), (11, "Alimentação > Restaurantes e Cafés")]
    monkeypatch.setattr(nordigen.requests, "post", lambda *a, **k: RespostaFalsa("2"))

    assert nordigen.escolher_por_llm("RESTAURANTE X", -20.0, opcoes) == 11


def test_escolher_por_llm_resposta_fora_de_gama_devolve_none(monkeypatch):
    monkeypatch.setattr(nordigen, "GROQ_API_KEY", "chave-falsa-para-teste")
    opcoes = [(10, "Alimentação > Supermercado")]
    monkeypatch.setattr(nordigen.requests, "post", lambda *a, **k: RespostaFalsa("99"))

    assert nordigen.escolher_por_llm("X", -20.0, opcoes) is None


def test_escolher_por_llm_resposta_sem_numero_devolve_none(monkeypatch):
    monkeypatch.setattr(nordigen, "GROQ_API_KEY", "chave-falsa-para-teste")
    opcoes = [(10, "Alimentação > Supermercado")]
    monkeypatch.setattr(nordigen.requests, "post", lambda *a, **k: RespostaFalsa("não sei"))

    assert nordigen.escolher_por_llm("X", -20.0, opcoes) is None


def test_escolher_por_llm_erro_http_devolve_none(monkeypatch):
    monkeypatch.setattr(nordigen, "GROQ_API_KEY", "chave-falsa-para-teste")
    opcoes = [(10, "Alimentação > Supermercado")]
    monkeypatch.setattr(nordigen.requests, "post", lambda *a, **k: RespostaFalsa("2", status_ok=False))

    assert nordigen.escolher_por_llm("X", -20.0, opcoes) is None


def test_escolher_por_llm_falha_de_rede_devolve_none(monkeypatch):
    monkeypatch.setattr(nordigen, "GROQ_API_KEY", "chave-falsa-para-teste")
    opcoes = [(10, "Alimentação > Supermercado")]

    def levanta_excecao(*a, **k):
        raise ConnectionError("API não está acessível")

    monkeypatch.setattr(nordigen.requests, "post", levanta_excecao)
    assert nordigen.escolher_por_llm("X", -20.0, opcoes) is None


def test_escolher_por_llm_sem_api_key_nao_chama_rede(monkeypatch):
    monkeypatch.setattr(nordigen, "GROQ_API_KEY", None)
    chamou_rede = []
    monkeypatch.setattr(nordigen.requests, "post", lambda *a, **k: chamou_rede.append(1))

    opcoes = [(10, "Alimentação > Supermercado")]
    assert nordigen.escolher_por_llm("X", -20.0, opcoes) is None
    assert chamou_rede == []

# ---
def test_categorizar_cai_em_fallback_quando_llm_nao_decide(client, headers_autenticado, monkeypatch):
    uid = uid_de(client, headers_autenticado)
    monkeypatch.setattr(nordigen, "escolher_por_llm", lambda *a, **k: None)

    categoria_id, origem = nordigen.categorizar("DESCRICAO TOTALMENTE DESCONHECIDA", -15.0, uid)

    assert origem == "sem_match"
    outros_pagamentos = id_categoria(client, headers_autenticado, "Outros Pagamentos", "Outros")
    assert categoria_id == outros_pagamentos

    conn = get_connection()
    em_cache = nordigen.buscar_em_cache(conn, "DESCRICAO TOTALMENTE DESCONHECIDA", uid)
    conn.close()
    assert em_cache == (outros_pagamentos, False)


def test_categorizar_fallback_distingue_entrada_e_saida(client, headers_autenticado, monkeypatch):
    uid = uid_de(client, headers_autenticado)
    monkeypatch.setattr(nordigen, "escolher_por_llm", lambda *a, **k: None)

    categoria_id, origem = nordigen.categorizar("RECEBIMENTO DESCONHECIDO", 200.0, uid)

    assert origem == "sem_match"
    outros_recebimentos = id_categoria(client, headers_autenticado, "Outros Recebimentos", "Outros")
    assert categoria_id == outros_recebimentos


def test_categorizar_com_categorias_quase_todas_eliminadas_ainda_resolve(client, headers_autenticado, monkeypatch):
    uid = uid_de(client, headers_autenticado)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categorias WHERE utilizador_id=%s AND NOT protegida AND parent_id IS NOT NULL", (uid,))
    conn.commit()
    cursor.close()
    conn.close()

    monkeypatch.setattr(nordigen, "escolher_por_llm", lambda descricao, valor, opcoes, contexto="": opcoes[0][0])

    categoria_id, origem = nordigen.categorizar("QUALQUER DESCRICAO", -10.0, uid)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT protegida FROM categorias WHERE id=%s", (categoria_id,))
    protegida = cursor.fetchone()[0]
    conn.close()
    assert protegida is True


def test_escolher_por_llm_resposta_zero_significa_nenhuma_opcao_aplica(monkeypatch):
    opcoes = [(10, "Categoria Estranha A"), (11, "Categoria Estranha B")]
    monkeypatch.setattr(nordigen.requests, "post", lambda *a, **k: RespostaFalsa("0"))
    assert nordigen.escolher_por_llm("X", -20.0, opcoes) is None


def test_resolver_categoria_fallback_e_imune_a_renomeacao(client, headers_autenticado, monkeypatch):
    uid = uid_de(client, headers_autenticado)
    monkeypatch.setattr(nordigen, "escolher_por_llm", lambda *a, **k: None)

    arvore_atual = client.get("/categorias/arvore", headers=headers_autenticado).json()
    outros_pagamentos = next(g for g in arvore_atual if g["nome"] == "Outros Pagamentos")
    client.put(f"/categorias/{outros_pagamentos['id']}", json={"nome": "Diversos"}, headers=headers_autenticado)

    categoria_id, origem = nordigen.categorizar("DESCRICAO QUALQUER", -10.0, uid)
    assert origem == "sem_match"
    assert categoria_id is not None