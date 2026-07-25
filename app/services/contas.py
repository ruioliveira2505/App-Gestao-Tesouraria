"""Regras de negócio de contas, âncora de saldo inicial e reconciliações.

Cada função recebe um cursor já aberto (a ligação/transacção é gerida pelo router) e
levanta ErroDominio para qualquer regra violada — não sabe o que é HTTP.
"""

import uuid
from datetime import date, timedelta

import psycopg2
from psycopg2.extensions import connection as PgConnection
from psycopg2.extras import RealDictCursor

from app.core.dominio import ErroDominio
from app.core.utils import fmt_data_pt
from app.schemas.contas import AjusteSaldoInput, ContaEditInput, ContaInput

# A âncora (saldo inicial + data) é um atributo próprio de cada conta, não uma
# reconciliação — mas para calcular "saldo numa data" precisamos de tratar a âncora e as
# reconciliações reais como pontos da mesma linha do tempo. Este CTE junta as duas fontes
# uma vez só, reutilizado por listar_contas/saldo_em_data (e por stats_saldo_diario, em
# services/estatisticas.py) em vez de cada um reimplementar a mesma junção.
PONTOS_SALDO_CTE = """
    pontos_saldo AS (
        SELECT id AS conta_id, data_ancora AS data, saldo_ancora AS saldo_real FROM contas
        UNION ALL
        SELECT conta_id, data, saldo_real FROM ajustes_saldo
    )
"""


def primeiro_movimento_data(cursor: RealDictCursor, conta_id: str) -> str | None:
    cursor.execute("SELECT MIN(data) AS data FROM movimentos WHERE conta_id=%s", (conta_id,))
    row = cursor.fetchone()
    return str(row["data"]) if row and row["data"] else None


def data_ancora(cursor: RealDictCursor, conta_id: str) -> str | None:
    """Data da âncora (o dia a partir do qual a conta passa a ter movimentos válidos) —
    atributo próprio de contas, não uma reconciliação (ver ARCHITECTURE.md)."""
    cursor.execute("SELECT data_ancora FROM contas WHERE id=%s", (conta_id,))
    row = cursor.fetchone()
    return str(row["data_ancora"]) if row else None


def listar_contas(cursor: RealDictCursor, uid: str) -> list[dict]:
    """Lista as contas do utilizador com o saldo actual já calculado."""
    cursor.execute("""
        WITH """ + PONTOS_SALDO_CTE + """
        SELECT c.id, c.nome, c.banco, c.iban, c.moeda, c.tipo,
               c.data_ancora AS inicio,
               a.saldo_real + COALESCE((
                   SELECT SUM(m.valor) FROM movimentos m
                   WHERE m.conta_id = c.id AND m.data > a.data AND m.data <= CURRENT_DATE
               ), 0) AS saldo
        FROM contas c
        CROSS JOIN LATERAL (
            SELECT saldo_real, data FROM pontos_saldo
            WHERE conta_id = c.id
            ORDER BY data DESC LIMIT 1
        ) a
        WHERE c.utilizador_id = %s
        ORDER BY c.nome
    """, (uid,))  # noqa: S608
    rows = cursor.fetchall()
    return [
        {
            "id": r["id"], "nome": r["nome"], "banco": r["banco"], "iban": r["iban"],
            "moeda": r["moeda"], "tipo": r["tipo"],
            # "inicio" é sempre a Data de Início de Movimentos já convertida (âncora + 1 dia),
            # nunca a data em bruto da âncora — é isto que aparece na tabela de Contas.
            "inicio": str(r["inicio"] + timedelta(days=1)),
            "saldo": float(r["saldo"]),
        }
        for r in rows
    ]


def criar_conta(cursor: RealDictCursor, uid: str, dados: ContaInput) -> None:
    """Cria a conta e a sua âncora de saldo inicial (dados.data é a data da âncora, não
    a Data de Início de Movimentos — essa é sempre âncora + 1 dia)."""
    if dados.data > date.today():
        raise ErroDominio(400, "DATA_FUTURA", "Não é possível criar uma conta com data futura.")

    conta_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO contas (id, nome, banco, iban, moeda, tipo, utilizador_id, data_ancora, saldo_ancora)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (conta_id, dados.nome, dados.banco, dados.iban, dados.moeda, dados.tipo, uid, dados.data, dados.saldo))


def editar_conta(cursor: RealDictCursor, uid: str, conta_id: str, dados: ContaEditInput) -> None:
    """Actualiza os dados descritivos da conta (nome/banco/iban/moeda/tipo) — não mexe em
    saldo nem na âncora; para isso ver editar_inicio_conta."""
    cursor.execute("""
        UPDATE contas SET nome=%s, banco=%s, iban=%s, moeda=%s, tipo=%s
        WHERE id=%s AND utilizador_id=%s
    """, (dados.nome, dados.banco, dados.iban, dados.moeda, dados.tipo, conta_id, uid))


def eliminar_conta(cursor: RealDictCursor, uid: str, conta_id: str, forcar: bool) -> None:
    """Elimina a conta; se tiver movimentos, exige forcar=true (elimina-os também)."""
    cursor.execute("SELECT COUNT(*) AS n FROM movimentos WHERE conta_id = %s AND utilizador_id = %s", (conta_id, uid))
    n = cursor.fetchone()["n"]

    if n > 0 and not forcar:
        raise ErroDominio(
            400, "CONTA_COM_MOVIMENTOS",
            f"Esta conta tem {n} movimento(s) associado(s). Ao eliminar a conta, estes movimentos também serão eliminados.",
            ctx={"n": n},
        )

    # movimentos e ajustes_saldo caem em ON DELETE CASCADE
    cursor.execute("DELETE FROM contas WHERE id = %s AND utilizador_id = %s", (conta_id, uid))


def obter_inicio_conta(cursor: RealDictCursor, uid: str, conta_id: str) -> dict:
    """Devolve a Data de Início de Movimentos e o saldo da âncora (âncora + 1 dia)."""
    cursor.execute("SELECT data_ancora, saldo_ancora FROM contas WHERE id=%s AND utilizador_id=%s", (conta_id, uid))
    row = cursor.fetchone()
    if not row:
        raise ErroDominio(404, "CONTA_NAO_ENCONTRADA", "Conta não encontrada")
    return {"data": str(row["data_ancora"] + timedelta(days=1)), "saldo_real": float(row["saldo_ancora"])}


def editar_inicio_conta(cursor: RealDictCursor, uid: str, conta_id: str, dados: AjusteSaldoInput, confirmar: bool) -> None:
    """Move a Data de Início de Movimentos (recua ou avança a âncora). Se avançar para lá
    de reconciliações já existentes, essas são eliminadas — só com confirmar=true."""
    cursor.execute("SELECT id FROM contas WHERE id=%s AND utilizador_id=%s", (conta_id, uid))
    if not cursor.fetchone():
        raise ErroDominio(404, "CONTA_NAO_ENCONTRADA", "Conta não encontrada")

    # "dados.data" chega como Data de Início de Movimentos (o que o utilizador vê e escreve);
    # a âncora, guardada na base de dados, fica sempre um dia antes.
    data_reconciliacao = dados.data - timedelta(days=1)

    if data_reconciliacao > date.today():
        raise ErroDominio(400, "INICIO_NO_FUTURO", "Não é possível definir um início de movimentos no futuro.")

    # Um movimento nunca pode existir antes da Data de Início de Movimentos.
    # primeiro_movimento_data devolve uma string (ISO) — comparação continua válida porque
    # datas ISO ordenam-se da mesma forma como texto e como data.
    primeiro_mov = primeiro_movimento_data(cursor, conta_id)
    if primeiro_mov and str(dados.data) > primeiro_mov:
        raise ErroDominio(
            400, "INICIO_APOS_PRIMEIRO_MOVIMENTO",
            f"Não é possível definir a Data de Início de Movimentos depois de {fmt_data_pt(primeiro_mov)}, já que tens um movimento registado nesse dia."
        )

    # Se a nova data ultrapassar reconciliações já existentes, essas passam a ficar
    # "antes" da âncora e têm de ser eliminadas — mas só com confirmação explícita.
    cursor.execute("SELECT id FROM ajustes_saldo WHERE conta_id=%s AND data <= %s", (conta_id, data_reconciliacao))
    afetadas = [r["id"] for r in cursor.fetchall()]
    if afetadas and not confirmar:
        raise ErroDominio(
            409, "INICIO_ULTRAPASSA_RECONCILIACOES",
            "A data de início de movimentos ultrapassa reconciliações existentes. Ao confirmar, essas reconciliações serão eliminadas."
        )
    if afetadas:
        cursor.execute("DELETE FROM ajustes_saldo WHERE id = ANY(%s)", (afetadas,))

    cursor.execute(
        "UPDATE contas SET data_ancora=%s, saldo_ancora=%s WHERE id=%s",
        (data_reconciliacao, dados.saldo_real, conta_id)
    )


def saldo_em_data(cursor: RealDictCursor, uid: str, conta_id: str, data: date) -> dict:
    """Saldo da conta numa data específica (âncora/reconciliação anterior + movimentos)."""
    cursor.execute("SELECT id FROM contas WHERE id=%s AND utilizador_id=%s", (conta_id, uid))
    if not cursor.fetchone():
        raise ErroDominio(404, "CONTA_NAO_ENCONTRADA", "Conta não encontrada")

    cursor.execute("""
        WITH """ + PONTOS_SALDO_CTE + """
        SELECT saldo_real, data FROM pontos_saldo
        WHERE conta_id=%s AND data <= %s
        ORDER BY data DESC LIMIT 1
    """, (conta_id, data))  # noqa: S608
    ponto = cursor.fetchone()
    if not ponto:
        raise ErroDominio(400, "SEM_RECONCILIACAO_ANTERIOR", "Não há nenhuma reconciliação anterior a esta data.")
    saldo_base, data_base = ponto["saldo_real"], ponto["data"]

    cursor.execute("""
        SELECT COALESCE(SUM(valor), 0) AS soma FROM movimentos
        WHERE conta_id=%s AND data > %s AND data <= %s
    """, (conta_id, data_base, data))
    soma_movimentos = float(cursor.fetchone()["soma"])
    saldo = float(saldo_base) + soma_movimentos
    return {"saldo": round(saldo, 2)}


def listar_ajustes_saldo(cursor: RealDictCursor, uid: str, conta_id: str) -> list[dict]:
    """Lista as reconciliações da conta (a âncora já não é uma linha desta tabela — ver
    ARCHITECTURE.md — por isso não há nada a excluir aqui). Uma query só (CTE + subquery
    correlacionada) em vez de uma SELECT extra por reconciliação."""
    cursor.execute("""
        WITH conta_uid AS (
            -- só produz uma linha se a conta pertencer ao utilizador — o INNER JOIN
            -- abaixo garante que, sem isso, o resultado inteiro fica vazio.
            SELECT id, data_ancora, saldo_ancora FROM contas WHERE id=%s AND utilizador_id=%s
        ),
        ordenados AS (
            SELECT a.id, a.data, a.saldo_real,
                   LAG(a.data) OVER (ORDER BY a.data) AS dt_anterior,
                   LAG(a.saldo_real) OVER (ORDER BY a.data) AS saldo_anterior
            FROM ajustes_saldo a
            JOIN conta_uid c ON a.conta_id = c.id
        )
        SELECT o.id, o.data, o.saldo_real,
               COALESCE(o.saldo_anterior, (SELECT saldo_ancora FROM conta_uid)) AS saldo_anterior,
               COALESCE((
                   SELECT SUM(m.valor) FROM movimentos m
                   WHERE m.conta_id=%s
                     AND m.data > COALESCE(o.dt_anterior, (SELECT data_ancora FROM conta_uid))
                     AND m.data <= o.data
               ), 0) AS soma_movimentos
        FROM ordenados o
        ORDER BY o.data ASC
    """, (conta_id, uid, conta_id))
    rows = cursor.fetchall()

    resultado = [
        {
            "id": r["id"], "data": str(r["data"]), "saldo_real": float(r["saldo_real"]),
            # soma feita em Decimal (o tipo que o psycopg2 devolve para numeric) antes de
            # arredondar/converter para float — evita somar o erro de arredondamento de
            # dois floats em vez de um só.
            "saldo_antes": round(float(r["saldo_anterior"] + r["soma_movimentos"]), 2),
        }
        for r in rows
    ]
    return sorted(resultado, key=lambda x: x["data"], reverse=True)


def criar_ajuste_saldo(cursor: RealDictCursor, conn: PgConnection, uid: str, conta_id: str, dados: AjusteSaldoInput) -> None:
    """Cria uma reconciliação nova — a data tem de ser posterior à âncora."""
    cursor.execute("SELECT data_ancora FROM contas WHERE id=%s AND utilizador_id=%s", (conta_id, uid))
    row = cursor.fetchone()
    if not row:
        raise ErroDominio(404, "CONTA_NAO_ENCONTRADA", "Conta não encontrada")

    if dados.data > date.today():
        raise ErroDominio(400, "DATA_FUTURA", "Não é possível reconciliar uma data futura.")

    if dados.data <= row["data_ancora"]:
        inicio_movimentos = row["data_ancora"] + timedelta(days=1)
        raise ErroDominio(
            400, "RECONCILIACAO_ANTES_DO_INICIO",
            f"Não é possível definir uma reconciliação antes de {fmt_data_pt(inicio_movimentos)}, a Data de Início de Movimentos desta conta."
        )

    try:
        cursor.execute("""
            INSERT INTO ajustes_saldo (conta_id, data, saldo_real) VALUES (%s, %s, %s)
        """, (conta_id, dados.data, dados.saldo_real))
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        raise ErroDominio(400, "RECONCILIACAO_DUPLICADA", "Não é possível ter duas reconciliações na mesma data.") from None


def editar_ajuste_saldo(cursor: RealDictCursor, uid: str, ajuste_id: int, dados: AjusteSaldoInput) -> None:
    """Corrige o saldo de uma reconciliação — a data nunca é editável (elimina e recria
    numa data nova, se for isso que precisas). A âncora já não é uma linha desta tabela,
    por isso não há como pedir para editar "a âncora" por engano aqui."""
    cursor.execute("""
        SELECT a.id FROM ajustes_saldo a
        JOIN contas c ON a.conta_id = c.id
        WHERE a.id=%s AND c.utilizador_id=%s
    """, (ajuste_id, uid))
    if not cursor.fetchone():
        raise ErroDominio(404, "RECONCILIACAO_NAO_ENCONTRADA", "Reconciliação não encontrada")

    cursor.execute("UPDATE ajustes_saldo SET saldo_real=%s WHERE id=%s", (dados.saldo_real, ajuste_id))


def eliminar_ajuste_saldo(cursor: RealDictCursor, uid: str, ajuste_id: int) -> None:
    """Elimina uma reconciliação. A âncora já não é uma linha desta tabela — para a mudar,
    usa PUT /contas/{id}/inicio; não há como a eliminar por aqui."""
    cursor.execute("""
        SELECT a.id FROM ajustes_saldo a
        JOIN contas c ON a.conta_id = c.id
        WHERE a.id=%s AND c.utilizador_id=%s
    """, (ajuste_id, uid))
    if not cursor.fetchone():
        raise ErroDominio(404, "RECONCILIACAO_NAO_ENCONTRADA", "Reconciliação não encontrada")

    cursor.execute("DELETE FROM ajustes_saldo WHERE id=%s", (ajuste_id,))
