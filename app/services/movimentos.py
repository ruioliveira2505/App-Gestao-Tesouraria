"""Regras de negócio de movimentos (transacções) e o fluxo de confirmação da
categorização automática.

Cada função recebe um cursor já aberto (a ligação/transacção é gerida pelo router) e
levanta ErroDominio para qualquer regra violada — não sabe o que é HTTP. Algumas também
recebem `conn`: a cache de categorização (guardar_em_cache) gere o seu próprio commit,
à parte da transacção principal, porque uma falha aí não deve invalidar o movimento já
guardado (ver _guardar_em_cache_seguro).

origem_cat marca de onde veio a categoria: "manual" (o utilizador escolheu/confirmou),
"cache" (veio de categorias_aprendidas já confirmada), "llm" (sugestão da IA, por
confirmar) ou "sem_match" (fallback, por confirmar). "llm"/"sem_match" é o que aparece
como pendente em /movimentos/pendentes/contagem.
"""

import logging
import uuid
from datetime import date, timedelta

from psycopg2.extensions import connection as PgConnection
from psycopg2.extras import RealDictCursor

from app.core.dominio import ErroDominio
from app.core.utils import fmt_data_pt, lista_sql
from app.schemas.movimentos import MovimentoInput
from app.services.categorizacao import guardar_em_cache
from app.services.contas import data_ancora

logger = logging.getLogger(__name__)


def _validar_data_movimento(cursor: RealDictCursor, conta_id: str, data: date) -> None:
    """Rejeita datas fora do intervalo válido: antes da Data de Início de Movimentos
    (âncora + 1 dia — nunca no próprio dia da âncora) ou no futuro. O limite inferior já
    existia; o superior faltava — contas e reconciliações já rejeitam data futura
    (DATA_FUTURA em services/contas.py), movimentos era a única das três que não."""
    if data > date.today():
        raise ErroDominio(400, "DATA_FUTURA", "Não é possível registar um movimento com data futura.")

    # data_ancora devolve uma string (ISO) — comparar como texto continua correcto porque
    # datas ISO ordenam-se da mesma forma como texto e como data.
    rec = data_ancora(cursor, conta_id)
    if rec and str(data) <= rec:
        inicio_movimentos = date.fromisoformat(rec) + timedelta(days=1)
        raise ErroDominio(
            400, "MOVIMENTO_ANTES_DO_INICIO",
            f"Não é possível registar um movimento antes de {fmt_data_pt(inicio_movimentos)}, a Data de Início de Movimentos desta conta.",
            ctx={"data": str(inicio_movimentos)},
        )


def _validar_categoria_direcao(cursor: RealDictCursor, categoria_id: int, valor: float, uid: str) -> None:
    cursor.execute("SELECT eh_recebimento FROM categorias WHERE id=%s AND utilizador_id=%s", (categoria_id, uid))
    row = cursor.fetchone()
    if not row:
        raise ErroDominio(404, "CATEGORIA_NAO_ENCONTRADA", "Categoria não encontrada")
    if (valor > 0) != row["eh_recebimento"]:
        direcao = "Entrada" if valor > 0 else "Saída"
        raise ErroDominio(
            400, "CATEGORIA_DIRECAO_ERRADA",
            f"Não é possível guardar este movimento: precisa de uma categoria de {direcao}.",
            ctx={"eh_recebimento": valor > 0},
        )


def _guardar_em_cache_seguro(
    conn: PgConnection, descricao: str, categoria_id: int, uid: str, eh_recebimento: bool, confirmado: bool,
) -> None:
    try:
        guardar_em_cache(conn, descricao, categoria_id, uid, eh_recebimento, confirmado=confirmado)
    except Exception:
        logger.exception("Falha ao gravar cache de categorização (não crítico — movimento já foi guardado)")


def listar_movimentos(
    cursor: RealDictCursor, uid: str, conta_id: str | None, categoria_id: str | None, direcao: str | None,
    data_de: str | None, data_ate: str | None, precisa_confirmacao: bool | None, limit: int | None, offset: int,
) -> list[dict]:
    """Lista movimentos com filtros. limit/offset são opcionais — sem eles devolve o
    conjunto completo, como sempre (nenhum cliente actual os envia ainda; a paginação
    fica disponível para quem precisar, sem mudar o comportamento por omissão)."""
    conta_cond, conta_vals = lista_sql("m.conta_id", conta_id)
    categoria_cond, categoria_vals = lista_sql("m.categoria_id", categoria_id)

    filtro_direcao = ""
    if direcao == "in":
        filtro_direcao = "AND m.valor > 0"
    elif direcao == "out":
        filtro_direcao = "AND m.valor < 0"

    filtro_confirmacao = ""
    if precisa_confirmacao is True:
        filtro_confirmacao = "AND m.origem_cat IN ('llm', 'sem_match')"
    elif precisa_confirmacao is False:
        filtro_confirmacao = "AND m.origem_cat NOT IN ('llm', 'sem_match')"

    limit_sql, limit_vals = ("LIMIT %s OFFSET %s", [limit, offset]) if limit is not None else ("", [])

    # conta_cond/categoria_cond/filtro_direcao/filtro_confirmacao/limit_sql são sempre
    # fragmentos fixos escolhidos em Python (nunca texto vindo do pedido); os valores
    # reais continuam todos parametrizados via %s — seguro apesar do aviso do bandit.
    cursor.execute("""
        SELECT m.id, m.conta_id, m.data, m.descricao, m.valor,
               m.categoria_id, c.nome AS categoria, c.slug AS categoria_slug,
               g.nome AS grupo, g.slug AS grupo_slug, m.origem_cat, c.protegida
        FROM movimentos m
        JOIN categorias c ON m.categoria_id = c.id
        JOIN categorias g ON c.parent_id = g.id
        WHERE m.utilizador_id = %s
          AND (%s IS NULL OR m.data >= %s)
          AND (%s IS NULL OR m.data <= %s)
    """ + conta_cond + categoria_cond + filtro_direcao + filtro_confirmacao + """
        ORDER BY m.data DESC, m.criado_em DESC
    """ + limit_sql, [uid, data_de, data_de, data_ate, data_ate, *conta_vals, *categoria_vals, *limit_vals])
    rows = cursor.fetchall()

    return [
        {
            "id": r["id"], "conta_id": r["conta_id"], "data": str(r["data"]), "descricao": r["descricao"],
            "valor": float(r["valor"]), "categoria_id": r["categoria_id"], "categoria": r["categoria"],
            "categoria_slug": r["categoria_slug"], "grupo": r["grupo"], "grupo_slug": r["grupo_slug"],
            "origem_cat": r["origem_cat"],
            "confirmado": r["origem_cat"] in ("manual", "cache"),
            "sem_categoria": r["protegida"],
        }
        for r in rows
    ]


def contar_movimentos_pendentes(cursor: RealDictCursor, uid: str) -> dict:
    """Quantos movimentos têm categorização automática por confirmar (origem_cat
    'llm' ou 'sem_match') — usado no aviso/banner de pendentes na UI."""
    cursor.execute("""
        SELECT COUNT(*) AS n FROM movimentos
        WHERE utilizador_id = %s AND origem_cat IN ('llm', 'sem_match')
    """, (uid,))
    return {"contagem": cursor.fetchone()["n"]}


def criar_movimento(cursor: RealDictCursor, conn: PgConnection, uid: str, dados: MovimentoInput) -> None:
    """Cria um movimento manual (origem_cat='manual', já confirmado por definição)."""
    _validar_categoria_direcao(cursor, dados.categoria_id, dados.valor, uid)
    _validar_data_movimento(cursor, dados.conta_id, dados.data)
    cursor.execute("""
        INSERT INTO movimentos (id, conta_id, data, descricao, valor, categoria_id, origem_cat, utilizador_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (str(uuid.uuid4()), dados.conta_id, dados.data, dados.descricao, dados.valor, dados.categoria_id, "manual", uid))
    conn.commit()
    _guardar_em_cache_seguro(conn, dados.descricao, dados.categoria_id, uid, dados.valor > 0, confirmado=True)


def editar_movimento(cursor: RealDictCursor, conn: PgConnection, uid: str, movimento_id: str, dados: MovimentoInput) -> None:
    """Edita um movimento; marca-o como confirmado e alimenta a cache de categorização."""
    _validar_categoria_direcao(cursor, dados.categoria_id, dados.valor, uid)
    _validar_data_movimento(cursor, dados.conta_id, dados.data)
    cursor.execute("""
        UPDATE movimentos
        SET conta_id=%s, data=%s, descricao=%s, valor=%s, categoria_id=%s, origem_cat='manual'
        WHERE id=%s AND utilizador_id=%s
    """, (dados.conta_id, dados.data, dados.descricao, dados.valor, dados.categoria_id, movimento_id, uid))
    conn.commit()
    _guardar_em_cache_seguro(conn, dados.descricao, dados.categoria_id, uid, dados.valor > 0, confirmado=True)


def eliminar_movimento(cursor: RealDictCursor, uid: str, movimento_id: str) -> None:
    """Elimina o movimento; não mexe na cache de categorização."""
    cursor.execute(
        "DELETE FROM movimentos WHERE id = %s AND utilizador_id = %s",
        (movimento_id, uid)
    )


def confirmar_movimento(cursor: RealDictCursor, conn: PgConnection, uid: str, movimento_id: str) -> None:
    """Aceita a categoria sugerida (llm/sem_match → manual) e reforça a cache."""
    cursor.execute(
        "SELECT descricao, categoria_id, valor FROM movimentos WHERE id=%s AND utilizador_id=%s",
        (movimento_id, uid)
    )
    row = cursor.fetchone()
    if not row:
        raise ErroDominio(404, "MOVIMENTO_NAO_ENCONTRADO", "Movimento não encontrado")
    descricao, categoria_id, valor = row["descricao"], row["categoria_id"], row["valor"]

    cursor.execute("UPDATE movimentos SET origem_cat='manual' WHERE id=%s", (movimento_id,))
    conn.commit()
    _guardar_em_cache_seguro(conn, descricao, categoria_id, uid, valor > 0, confirmado=True)


def confirmar_todos_os_pendentes(cursor: RealDictCursor, conn: PgConnection, uid: str) -> dict:
    """Confirma em massa todos os movimentos pendentes do utilizador."""
    cursor.execute("""
        SELECT DISTINCT descricao, categoria_id, valor FROM movimentos
        WHERE utilizador_id=%s AND origem_cat IN ('llm', 'sem_match')
    """, (uid,))
    pendentes = cursor.fetchall()

    cursor.execute("""
        UPDATE movimentos SET origem_cat='manual'
        WHERE utilizador_id=%s AND origem_cat IN ('llm', 'sem_match')
    """, (uid,))
    conn.commit()

    for p in pendentes:
        _guardar_em_cache_seguro(conn, p["descricao"], p["categoria_id"], uid, p["valor"] > 0, confirmado=True)

    return {"ok": True, "confirmados": len(pendentes)}
