import json
import requests
import re
from database import get_connection


REGRAS = [
    # Trabalho
    ("salario",               ("Trabalho", "Salário")),
    ("vencimento",            ("Trabalho", "Salário")),

    # Habitação
    ("edp ",                  ("Habitação", "Água, Eletricidade e Gás")),
    ("galp",                  ("Transportes", "Combustível")),
    ("nos ",                  ("Habitação", "Telecomunicações")),
    ("meo ",                  ("Habitação", "Telecomunicações")),
    ("vodafone",              ("Habitação", "Telecomunicações")),

    # Alimentação
    ("continente",            ("Alimentação", "Supermercado")),
    ("pingo doce",            ("Alimentação", "Supermercado")),
    ("aldi",                  ("Alimentação", "Supermercado")),
    ("lidl",                  ("Alimentação", "Supermercado")),
    ("mercadona",             ("Alimentação", "Supermercado")),
    ("intermarche",           ("Alimentação", "Supermercado")),
    ("minipreco",             ("Alimentação", "Supermercado")),

    # Transportes
    ("bp ",                   ("Transportes", "Combustível")),
    ("repsol",                ("Transportes", "Combustível")),
    ("cepsa",                 ("Transportes", "Combustível")),
    ("via verde",             ("Transportes", "Portagens e Estacionamento")),
    ("cp ",                   ("Transportes", "Transportes Públicos e TVDE")),
    ("uber ",                 ("Transportes", "Transportes Públicos e TVDE")),
    ("bolt ",                 ("Transportes", "Transportes Públicos e TVDE")),

    # Impostos
    ("pagamento irs",         ("Impostos", "IRS")),
    ("at ",                   ("Impostos", "Outros")),
    ("iuc ",                  ("Impostos", "IUC")),
    ("imi ",                  ("Impostos", "IMI")),

    # Seguros
    ("medis",                 ("Seguros", "Saúde")),
    ("multicare",             ("Seguros", "Saúde")),

    # Entretenimento
    ("netflix",               ("Entretenimento", "Subscrições")),
    ("spotify",               ("Entretenimento", "Subscrições")),
    ("hbo",                   ("Entretenimento", "Subscrições")),
    ("disney",                ("Entretenimento", "Subscrições")),
    ("amazon prime",          ("Entretenimento", "Subscrições")),
]


def categorizar_por_regras(descricao):
    descricao_lower = descricao.lower()
    for palavra, (grupo, categoria) in REGRAS:
        if palavra in descricao_lower:
            return grupo, categoria
    return None


def resolver_categoria_id(conn, grupo, categoria, utilizador_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id FROM categorias c
        JOIN categorias g ON c.parent_id = g.id
        WHERE g.nome = %s AND c.nome = %s AND c.utilizador_id = %s
    """, (grupo, categoria, utilizador_id))
    row = cursor.fetchone()
    cursor.close()
    return row[0] if row else None


def buscar_em_cache(conn, descricao, utilizador_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT categoria_id FROM categorias_aprendidas
        WHERE descricao = %s AND utilizador_id = %s
    """, (descricao, utilizador_id))
    row = cursor.fetchone()
    cursor.close()
    return row[0] if row else None


def guardar_em_cache(conn, descricao, categoria_id, utilizador_id):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO categorias_aprendidas (descricao, categoria_id, utilizador_id)
        VALUES (%s, %s, %s)
        ON CONFLICT (descricao, utilizador_id)
        DO UPDATE SET categoria_id = EXCLUDED.categoria_id
    """, (descricao, categoria_id, utilizador_id))
    conn.commit()
    cursor.close()


def listar_categorias_planas(conn, utilizador_id, valor):
    """Lista todas as categorias finais (sem filhos) do lado certo da árvore,
    com o caminho completo, ex: 'Habitação > Água, Eletricidade e Gás'."""
    cursor = conn.cursor()
    cursor.execute("""
        WITH RECURSIVE arvore AS (
            SELECT id, parent_id, nome AS caminho, eh_recebimento
            FROM categorias
            WHERE utilizador_id = %s AND parent_id IS NULL

            UNION ALL

            SELECT c.id, c.parent_id, a.caminho || ' > ' || c.nome, a.eh_recebimento
            FROM categorias c
            JOIN arvore a ON c.parent_id = a.id
        )
        SELECT a.id, a.caminho
        FROM arvore a
        WHERE a.eh_recebimento = %s
          AND NOT EXISTS (SELECT 1 FROM categorias f WHERE f.parent_id = a.id)
        ORDER BY a.caminho
    """, (utilizador_id, valor > 0))
    rows = cursor.fetchall()
    cursor.close()
    return rows


def escolher_por_llm(descricao, valor, opcoes, contexto=""):
    """opcoes: lista de (id, nome). Devolve o id escolhido ou None."""
    direcao = "um recebimento (dinheiro a entrar)" if valor > 0 else "um pagamento (dinheiro a saír)"
    lista_texto = "\n".join(f"{i+1}. {nome}" for i, (_, nome) in enumerate(opcoes))

    prompt = (
        f"Este é {direcao} numa conta bancária pessoal.{contexto}\n\n"
        f'Descrição do movimento: "{descricao}"\n\n'
        "Escolhe a opção mais adequada desta lista, indicando APENAS o número "
        "correspondente, sem mais nenhum texto:\n\n"
        f"{lista_texto}"
    )

    try:
        resposta = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3.1:8b", "prompt": prompt, "stream": False},
            timeout=60,
        )
        texto = resposta.json()["response"].strip()
        match = re.search(r"\d+", texto)
        if match:
            indice = int(match.group()) - 1
            if 0 <= indice < len(opcoes):
                return opcoes[indice][0]
        return None
    except Exception as e:
        print(f"Erro ao chamar o Ollama: {e}")
        return None


def categorizar_por_llm(descricao, valor, conn, utilizador_id):
    categorias_disponiveis = listar_categorias_planas(conn, utilizador_id, valor)
    if not categorias_disponiveis:
        return None
    return escolher_por_llm(descricao, valor, categorias_disponiveis)


def categorizar(descricao, valor, utilizador_id, conn=None):
    """Devolve (categoria_id, origem) para um movimento."""
    proprio_conn = conn is None
    if proprio_conn:
        conn = get_connection()

    try:
        resultado_regra = categorizar_por_regras(descricao)
        if resultado_regra:
            grupo, categoria = resultado_regra
            categoria_id = resolver_categoria_id(conn, grupo, categoria, utilizador_id)
            if categoria_id:
                return categoria_id, "regra"

        categoria_id = buscar_em_cache(conn, descricao, utilizador_id)
        if categoria_id:
            return categoria_id, "cache"

        categoria_id = categorizar_por_llm(descricao, valor, conn, utilizador_id)
        if categoria_id:
            guardar_em_cache(conn, descricao, categoria_id, utilizador_id)
            return categoria_id, "llm"

        grupo_fallback = "Outros Recebimentos" if valor > 0 else "Outros Pagamentos"
        categoria_id = resolver_categoria_id(conn, grupo_fallback, "Outros", utilizador_id)
        return categoria_id, "sem_match"
    finally:
        if proprio_conn:
            conn.close()


if __name__ == "__main__":
    with open("dados_mock.json", "r", encoding="utf-8") as f:
        dados = json.load(f)

    conn = get_connection()

    print(f"{'DATA':<12} {'DESCRIÇÃO':<38} {'VALOR':>10}  ORIGEM")
    print("-" * 80)

    for m in dados["movimentos"]:
        categoria_id, origem = categorizar(m["descricao"], m["valor"], 1, conn)
        print(f"{m['data']:<12} {m['descricao']:<38} {m['valor']:>10.2f}  [{origem}] id={categoria_id}")

    conn.close()