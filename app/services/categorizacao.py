"""Categorização automática de movimentos — cache aprendida primeiro, depois LLM (API da
Groq), com fallback para a categoria "Outros" protegida da direcção certa.

`categorizar()` é o ponto de entrada usado pelos serviços de movimentos (ver
services/movimentos.py::_guardar_em_cache_seguro) e por scripts/seed_dev.py; devolve sempre
um (categoria_id, origem) — origem é 'cache' | 'llm' | 'sem_match' (nunca 'manual', que só
o utilizador escolhe directamente). Nenhuma função aqui depende do FastAPI.
"""

import logging
import re

import requests
from psycopg2.extensions import connection as PgConnection
from psycopg2.extras import RealDictCursor

from app.core.config import settings
from app.db.database import get_connection, release_connection

logger = logging.getLogger(__name__)

GROQ_API_KEY = settings.GROQ_API_KEY
GROQ_MODEL   = settings.GROQ_MODEL


# ─── BD helpers ──────────────────────────────────────────────────────────────

def resolver_categoria_fallback(conn: PgConnection, eh_recebimento: bool, utilizador_id: str) -> int | None:
    # Usa 'protegida' + direção — imune a renomeações na árvore de categorias.
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT id FROM categorias
        WHERE protegida = true AND eh_recebimento = %s AND utilizador_id = %s
    """, (eh_recebimento, utilizador_id))
    row = cursor.fetchone()
    cursor.close()
    return row["id"] if row else None


def buscar_em_cache(conn: PgConnection, descricao: str, utilizador_id: str, eh_recebimento: bool) -> tuple[int, bool] | None:
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT categoria_id, confirmado FROM categorias_aprendidas
        WHERE descricao = %s AND utilizador_id = %s AND eh_recebimento = %s
    """, (descricao, utilizador_id, eh_recebimento))
    row = cursor.fetchone()
    cursor.close()
    return (row["categoria_id"], row["confirmado"]) if row else None


def guardar_em_cache(
    conn: PgConnection, descricao: str, categoria_id: int, utilizador_id: str,
    eh_recebimento: bool, confirmado: bool = False,
) -> None:
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        INSERT INTO categorias_aprendidas (descricao, categoria_id, utilizador_id, eh_recebimento, confirmado)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (descricao, utilizador_id, eh_recebimento)
        DO UPDATE SET categoria_id = EXCLUDED.categoria_id, confirmado = EXCLUDED.confirmado
    """, (descricao, categoria_id, utilizador_id, eh_recebimento, confirmado))
    conn.commit()
    cursor.close()


def listar_categorias_planas(conn: PgConnection, utilizador_id: str, valor: float) -> list[tuple[int, str]]:
    """Devolve uma lista de tuplos (id, caminho) — escolher_por_llm depende deste formato."""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
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
          AND a.parent_id IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM categorias f WHERE f.parent_id = a.id)
        ORDER BY a.caminho
    """, (utilizador_id, valor > 0))
    rows = cursor.fetchall()
    cursor.close()
    return [(r["id"], r["caminho"]) for r in rows]


# ─── LLM ─────────────────────────────────────────────────────────────────────

def escolher_por_llm(descricao: str, valor: float, opcoes: list[tuple[int, str]], contexto: str = "") -> int | None:
    # Devolve o id escolhido, ou None se o LLM recusar ('0'), falhar ou resposta ilegível.
    direcao = "um recebimento (dinheiro a entrar)" if valor > 0 else "um pagamento (dinheiro a saír)"
    lista_texto = "\n".join(f"{i+1}. {nome}" for i, (_, nome) in enumerate(opcoes))

    prompt = (
        f"Este é {direcao} numa conta bancária pessoal.{contexto}\n\n"
        f'Descrição do movimento: "{descricao}"\n\n'
        "Escolhe a opção mais adequada desta lista, indicando APENAS o número "
        "correspondente, sem mais nenhum texto. Se nenhuma das opções descrever "
        "bem este movimento, responde 0.\n\n"
        "0. Nenhuma das opções se aplica\n"
        f"{lista_texto}"
    )

    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY não está definida — a saltar categorização por LLM.")
        return None

    try:
        resposta = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "max_tokens": 10,
            },
            timeout=15,
        )
        resposta.raise_for_status()
        texto = resposta.json()["choices"][0]["message"]["content"].strip()
        match = re.search(r"\d+", texto)
        if not match:
            return None
        indice = int(match.group()) - 1
        if 0 <= indice < len(opcoes):
            return opcoes[indice][0]
        return None
    except Exception as e:
        logger.error("Erro ao chamar a API da Groq: %s", e)
        return None


def categorizar_por_llm(descricao: str, valor: float, conn: PgConnection, utilizador_id: str) -> int | None:
    categorias_disponiveis = listar_categorias_planas(conn, utilizador_id, valor)
    if not categorias_disponiveis:
        return None
    return escolher_por_llm(descricao, valor, categorias_disponiveis)


# ─── Orquestração ─────────────────────────────────────────────────────────────
# origem possível: 'manual' | 'cache' | 'llm' | 'sem_match'

def categorizar(descricao: str, valor: float, utilizador_id: str, conn: PgConnection | None = None) -> tuple[int | None, str]:
    proprio_conn = conn is None
    if proprio_conn:
        conn = get_connection()

    eh_recebimento = valor > 0

    try:
        em_cache = buscar_em_cache(conn, descricao, utilizador_id, eh_recebimento)
        if em_cache:
            categoria_id, confirmado = em_cache
            return categoria_id, ("cache" if confirmado else "llm")

        categoria_id = categorizar_por_llm(descricao, valor, conn, utilizador_id)
        if categoria_id:
            guardar_em_cache(conn, descricao, categoria_id, utilizador_id, eh_recebimento, confirmado=False)
            return categoria_id, "llm"

        categoria_id = resolver_categoria_fallback(conn, eh_recebimento, utilizador_id)
        if categoria_id:
            guardar_em_cache(conn, descricao, categoria_id, utilizador_id, eh_recebimento, confirmado=False)
        return categoria_id, "sem_match"
    finally:
        if proprio_conn:
            release_connection(conn)