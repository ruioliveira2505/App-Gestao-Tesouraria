import uuid
from datetime import date, timedelta

import psycopg2
from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import utilizador_atual
from app.db.database import get_connection, release_connection
from app.schemas.contas import AjusteSaldoInput, ContaEditInput, ContaInput
from app.services.reconciliacoes import atualizar_saldo_atual, primeiro_movimento_data

router = APIRouter()


# ─── contas ───────────────────────────────────────────────────────────────────

@router.get("/contas")
def listar_contas(utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT c.id, c.nome, c.banco, c.iban, c.moeda, c.tipo,
                   (SELECT MIN(data) FROM ajustes_saldo WHERE conta_id = c.id) AS inicio,
                   a.saldo_real + COALESCE((
                       SELECT SUM(m.valor) FROM movimentos m
                       WHERE m.conta_id = c.id AND m.data > a.data AND m.data <= CURRENT_DATE
                   ), 0) AS saldo
            FROM contas c
            CROSS JOIN LATERAL (
                SELECT saldo_real, data FROM ajustes_saldo
                WHERE conta_id = c.id
                ORDER BY data DESC LIMIT 1
            ) a
            WHERE c.utilizador_id = %s
            ORDER BY c.nome
        """, (utilizador["sub"],))
        rows = cursor.fetchall()
    finally:
        cursor.close()
        release_connection(conn)
    return [
        {
            "id": r[0], "nome": r[1], "banco": r[2], "iban": r[3], "moeda": r[4], "tipo": r[5],
            # "inicio" é sempre a Data de Início de Movimentos já convertida (âncora + 1 dia),
            # nunca a data em bruto da âncora — é isto que aparece na tabela de Contas.
            "inicio": str(r[6] + timedelta(days=1)),
            "saldo": float(r[7]),
        }
        for r in rows
    ]


@router.post("/contas")
def criar_conta(dados: ContaInput, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if dados.data > str(date.today()):
            raise HTTPException(status_code=400, detail="Não é possível criar uma conta com data futura.")

        conta_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO contas (id, nome, banco, iban, moeda, saldo, tipo, utilizador_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (conta_id, dados.nome, dados.banco, dados.iban, dados.moeda, dados.saldo, dados.tipo, utilizador["sub"]))
        cursor.execute("""
            INSERT INTO ajustes_saldo (conta_id, data, saldo_real) VALUES (%s, %s, %s)
        """, (conta_id, dados.data, dados.saldo))
        conn.commit()
    finally:
        cursor.close()
        release_connection(conn)
    return {"ok": True}


@router.put("/contas/{conta_id}")
def editar_conta(conta_id: str, dados: ContaEditInput, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE contas SET nome=%s, banco=%s, iban=%s, moeda=%s, tipo=%s
            WHERE id=%s AND utilizador_id=%s
        """, (dados.nome, dados.banco, dados.iban, dados.moeda, dados.tipo, conta_id, utilizador["sub"]))
        conn.commit()
    finally:
        cursor.close()
        release_connection(conn)
    return {"ok": True}


@router.delete("/contas/{conta_id}")
def eliminar_conta(conta_id: str, forcar: bool = False, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]
    try:
        cursor.execute("SELECT COUNT(*) FROM movimentos WHERE conta_id = %s AND utilizador_id = %s", (conta_id, uid))
        n = cursor.fetchone()[0]

        if n > 0 and not forcar:
            raise HTTPException(
                status_code=400,
                detail=f"Esta conta tem {n} movimento(s) associado(s). Ao eliminar a conta, estes movimentos também serão eliminados."
            )

        if n > 0:
            cursor.execute("DELETE FROM movimentos WHERE conta_id = %s AND utilizador_id = %s", (conta_id, uid))

        cursor.execute("DELETE FROM ajustes_saldo WHERE conta_id = %s", (conta_id,))
        cursor.execute("DELETE FROM contas WHERE id = %s AND utilizador_id = %s", (conta_id, uid))
        conn.commit()
    finally:
        cursor.close()
        release_connection(conn)
    return {"ok": True}


# ─── Data de Início de Movimentos / Saldo Inicial (a âncora da conta —
#     ver reflexão no chat sobre porque é tratada à parte de "Reconciliações") ─

@router.get("/contas/{conta_id}/inicio")
def obter_inicio_conta(conta_id: str, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]
    try:
        cursor.execute("SELECT id FROM contas WHERE id=%s AND utilizador_id=%s", (conta_id, uid))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Conta não encontrada")

        cursor.execute("""
            SELECT data, saldo_real FROM ajustes_saldo
            WHERE conta_id=%s ORDER BY data ASC LIMIT 1
        """, (conta_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Esta conta não tem uma data de início definida.")
    finally:
        cursor.close()
        release_connection(conn)
    return {"data": str(row[0] + timedelta(days=1)), "saldo_real": float(row[1])}


@router.put("/contas/{conta_id}/inicio")
def editar_inicio_conta(
    conta_id: str,
    dados: AjusteSaldoInput,
    confirmar: bool = False,
    utilizador: dict = Depends(utilizador_atual),
):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]
    try:
        cursor.execute("SELECT id FROM contas WHERE id=%s AND utilizador_id=%s", (conta_id, uid))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Conta não encontrada")

        cursor.execute("SELECT id, data FROM ajustes_saldo WHERE conta_id=%s ORDER BY data ASC LIMIT 1", (conta_id,))
        mais_antiga = cursor.fetchone()
        if not mais_antiga:
            raise HTTPException(status_code=404, detail="Esta conta não tem uma data de início definida.")
        mais_antiga_id = mais_antiga[0]

        # "dados.data" chega como Data de Início de Movimentos (o que o utilizador vê e escreve);
        # a âncora, guardada na base de dados, fica sempre um dia antes.
        data_inicio_movimentos = date.fromisoformat(dados.data)
        data_reconciliacao = data_inicio_movimentos - timedelta(days=1)
        data_reconciliacao_str = str(data_reconciliacao)

        if data_reconciliacao_str > str(date.today()):
            raise HTTPException(status_code=400, detail="Não é possível definir um início de movimentos no futuro.")

        # Um movimento nunca pode existir antes da Data de Início de Movimentos.
        primeiro_mov = primeiro_movimento_data(cursor, conta_id)
        if primeiro_mov and dados.data > primeiro_mov:
            raise HTTPException(
                status_code=400,
                detail=f"Não é possível definir a Data de Início de Movimentos depois de {primeiro_mov}, já que tens um movimento registado nesse dia."
            )

        # Se a nova data ultrapassar reconciliações já existentes, essas passam a ficar
        # "antes" da âncora e têm de ser eliminadas — mas só com confirmação explícita.
        cursor.execute(
            "SELECT id FROM ajustes_saldo WHERE conta_id=%s AND id != %s AND data <= %s",
            (conta_id, mais_antiga_id, data_reconciliacao_str)
        )
        afetadas = [r[0] for r in cursor.fetchall()]
        if afetadas and not confirmar:
            raise HTTPException(
                status_code=409,
                detail="A data de início de movimentos ultrapassa reconciliações existentes. Ao confirmar, essas reconciliações serão eliminadas."
            )
        if afetadas:
            cursor.execute("DELETE FROM ajustes_saldo WHERE id = ANY(%s)", (afetadas,))

        cursor.execute("UPDATE ajustes_saldo SET data=%s, saldo_real=%s WHERE id=%s", (data_reconciliacao_str, dados.saldo_real, mais_antiga_id))
        atualizar_saldo_atual(cursor, conta_id)
        conn.commit()
    finally:
        cursor.close()
        release_connection(conn)
    return {"ok": True}


# ─── ajustes de saldo (reconciliações — nunca inclui a âncora, ver acima) ────

@router.get("/contas/{conta_id}/saldo-em-data")
def saldo_em_data(conta_id: str, data: str, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]
    try:
        cursor.execute("SELECT id FROM contas WHERE id=%s AND utilizador_id=%s", (conta_id, uid))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Conta não encontrada")

        cursor.execute("""
            SELECT saldo_real, data FROM ajustes_saldo
            WHERE conta_id=%s AND data <= %s
            ORDER BY data DESC LIMIT 1
        """, (conta_id, data))
        ancora = cursor.fetchone()
        if not ancora:
            raise HTTPException(status_code=400, detail="Não há nenhuma reconciliação anterior a esta data.")
        saldo_ancora, data_ancora = ancora

        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0) FROM movimentos
            WHERE conta_id=%s AND data > %s AND data <= %s
        """, (conta_id, data_ancora, data))
        soma_movimentos = float(cursor.fetchone()[0])
        saldo = float(saldo_ancora) + soma_movimentos
    finally:
        cursor.close()
        release_connection(conn)
    return {"saldo": round(saldo, 2)}


@router.get("/contas/{conta_id}/ajustes-saldo")
def listar_ajustes_saldo(conta_id: str, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]
    try:
        cursor.execute("""
            SELECT a.id, a.data, a.saldo_real,
                   LAG(a.data) OVER (ORDER BY a.data), LAG(a.saldo_real) OVER (ORDER BY a.data)
            FROM ajustes_saldo a
            JOIN contas c ON a.conta_id = c.id
            WHERE a.conta_id=%s AND c.utilizador_id=%s
            ORDER BY a.data ASC
        """, (conta_id, uid))
        rows = cursor.fetchall()

        resultado = []
        for ajuste_id, dt, saldo_real, dt_anterior, saldo_anterior in rows:
            if dt_anterior is None:
                # é a âncora (Data de Início de Movimentos) — não aparece na lista de reconciliações
                continue
            cursor.execute("""
                SELECT COALESCE(SUM(valor), 0) FROM movimentos
                WHERE conta_id=%s AND data > %s AND data <= %s
            """, (conta_id, dt_anterior, dt))
            soma_movimentos = float(cursor.fetchone()[0])
            saldo_esperado = float(saldo_anterior) + soma_movimentos
            resultado.append({"id": ajuste_id, "data": str(dt), "saldo_real": float(saldo_real), "saldo_antes": round(saldo_esperado, 2)})
    finally:
        cursor.close()
        release_connection(conn)
    return sorted(resultado, key=lambda x: x["data"], reverse=True)


@router.post("/contas/{conta_id}/ajustes-saldo")
def criar_ajuste_saldo(conta_id: str, dados: AjusteSaldoInput, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]
    try:
        cursor.execute("SELECT id FROM contas WHERE id=%s AND utilizador_id=%s", (conta_id, uid))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Conta não encontrada")

        if dados.data > str(date.today()):
            raise HTTPException(status_code=400, detail="Não é possível reconciliar uma data futura.")

        cursor.execute("SELECT MIN(data) FROM ajustes_saldo WHERE conta_id=%s", (conta_id,))
        mais_antiga_row = cursor.fetchone()
        mais_antiga = mais_antiga_row[0] if mais_antiga_row and mais_antiga_row[0] else None
        if mais_antiga and date.fromisoformat(dados.data) <= mais_antiga:
            inicio_movimentos = mais_antiga + timedelta(days=1)
            raise HTTPException(
                status_code=400,
                detail=f"Não é possível definir uma reconciliação antes de {inicio_movimentos}, a Data de Início de Movimentos desta conta."
            )

        try:
            cursor.execute("""
                INSERT INTO ajustes_saldo (conta_id, data, saldo_real) VALUES (%s, %s, %s)
            """, (conta_id, dados.data, dados.saldo_real))
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            raise HTTPException(status_code=400, detail="Não é possível ter duas reconciliações na mesma data.")

        atualizar_saldo_atual(cursor, conta_id)
        conn.commit()
    finally:
        cursor.close()
        release_connection(conn)
    return {"ok": True}


@router.put("/ajustes-saldo/{ajuste_id}")
def editar_ajuste_saldo(ajuste_id: int, dados: AjusteSaldoInput, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]
    try:
        cursor.execute("""
            SELECT a.conta_id FROM ajustes_saldo a
            JOIN contas c ON a.conta_id = c.id
            WHERE a.id=%s AND c.utilizador_id=%s
        """, (ajuste_id, uid))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Reconciliação não encontrada")
        conta_id = row[0]

        cursor.execute("SELECT id FROM ajustes_saldo WHERE conta_id=%s ORDER BY data ASC LIMIT 1", (conta_id,))
        mais_antiga_id = cursor.fetchone()[0]
        if ajuste_id == mais_antiga_id:
            raise HTTPException(
                status_code=400,
                detail="Esta é a Data Anterior ao Início de Movimentos desta conta. Para a editar, fazê-lo através de 'Editar Conta'."
            )

        # A data de uma reconciliação nunca é editável — só o saldo. Para corrigir a data,
        # elimina esta reconciliação e cria uma nova na data certa.
        cursor.execute("UPDATE ajustes_saldo SET saldo_real=%s WHERE id=%s", (dados.saldo_real, ajuste_id))

        atualizar_saldo_atual(cursor, conta_id)
        conn.commit()
    finally:
        cursor.close()
        release_connection(conn)
    return {"ok": True}


@router.delete("/ajustes-saldo/{ajuste_id}")
def eliminar_ajuste_saldo(ajuste_id: int, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]
    try:
        cursor.execute("""
            SELECT a.conta_id FROM ajustes_saldo a
            JOIN contas c ON a.conta_id = c.id
            WHERE a.id=%s AND c.utilizador_id=%s
        """, (ajuste_id, uid))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Reconciliação não encontrada")
        conta_id = row[0]

        cursor.execute("SELECT id FROM ajustes_saldo WHERE conta_id=%s ORDER BY data ASC LIMIT 1", (conta_id,))
        mais_antiga_id = cursor.fetchone()[0]
        if ajuste_id == mais_antiga_id:
            raise HTTPException(
                status_code=400,
                detail="Esta é a Data Anterior ao Início de Movimentos desta conta. Para a eliminar, terá de eliminar a conta."
            )

        cursor.execute("DELETE FROM ajustes_saldo WHERE id=%s", (ajuste_id,))
        atualizar_saldo_atual(cursor, conta_id)
        conn.commit()
    finally:
        cursor.close()
        release_connection(conn)
    return {"ok": True}