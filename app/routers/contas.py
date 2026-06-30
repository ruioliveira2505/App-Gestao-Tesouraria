import uuid
from datetime import date

import psycopg2
from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import utilizador_atual
from app.db.database import get_connection, release_connection, release_connection
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
                   a.saldo_real + COALESCE((
                       SELECT SUM(m.valor) FROM movimentos m
                       WHERE m.conta_id = c.id AND m.data >= a.data AND m.data <= CURRENT_DATE
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
        {"id": r[0], "nome": r[1], "banco": r[2], "iban": r[3], "moeda": r[4], "tipo": r[5], "saldo": float(r[6])}
        for r in rows
    ]


@router.post("/contas")
def criar_conta(dados: ContaInput, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        conta_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO contas (id, nome, banco, iban, moeda, saldo, tipo, utilizador_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (conta_id, dados.nome, dados.banco, dados.iban, dados.moeda, dados.saldo, dados.tipo, utilizador["sub"]))
        cursor.execute("""
            INSERT INTO ajustes_saldo (conta_id, data, saldo_real) VALUES (%s, CURRENT_DATE, %s)
        """, (conta_id, dados.saldo))
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
            raise HTTPException(status_code=400, detail=f"Esta conta tem {n} movimento(s) associados. Confirma a eliminação para os apagar também.")

        if n > 0:
            cursor.execute("DELETE FROM movimentos WHERE conta_id = %s AND utilizador_id = %s", (conta_id, uid))

        cursor.execute("DELETE FROM ajustes_saldo WHERE conta_id = %s", (conta_id,))
        cursor.execute("DELETE FROM contas WHERE id = %s AND utilizador_id = %s", (conta_id, uid))
        conn.commit()
    finally:
        cursor.close()
        release_connection(conn)
    return {"ok": True}


# ─── ajustes de saldo (reconciliações) ───────────────────────────────────────

@router.get("/contas/{conta_id}/ajustes-saldo")
def listar_ajustes_saldo(conta_id: str, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT a.id, a.data, a.saldo_real FROM ajustes_saldo a
            JOIN contas c ON a.conta_id = c.id
            WHERE a.conta_id=%s AND c.utilizador_id=%s
            ORDER BY a.data DESC
        """, (conta_id, utilizador["sub"]))
        rows = cursor.fetchall()
    finally:
        cursor.close()
        release_connection(conn)
    return [{"id": r[0], "data": str(r[1]), "saldo_real": float(r[2])} for r in rows]


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

        try:
            cursor.execute("""
                INSERT INTO ajustes_saldo (conta_id, data, saldo_real) VALUES (%s, %s, %s)
            """, (conta_id, dados.data, dados.saldo_real))
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            raise HTTPException(status_code=400, detail="Já existe uma reconciliação nessa data.")

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

        if dados.data > str(date.today()):
            raise HTTPException(status_code=400, detail="Não é possível reconciliar uma data futura.")

        cursor.execute("SELECT MIN(data) FROM ajustes_saldo WHERE conta_id=%s AND id != %s", (conta_id, ajuste_id))
        outra_row = cursor.fetchone()
        outras_mais_antiga = str(outra_row[0]) if outra_row and outra_row[0] else None
        nova_mais_antiga = min(outras_mais_antiga, dados.data) if outras_mais_antiga else dados.data

        primeiro_mov = primeiro_movimento_data(cursor, conta_id)
        if primeiro_mov and nova_mais_antiga > primeiro_mov:
            raise HTTPException(
                status_code=400,
                detail=f"Esta conta tem movimentos a partir de {primeiro_mov}. A reconciliação mais antiga não pode ficar depois dessa data."
            )

        try:
            cursor.execute("UPDATE ajustes_saldo SET data=%s, saldo_real=%s WHERE id=%s", (dados.data, dados.saldo_real, ajuste_id))
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            raise HTTPException(status_code=400, detail="Já existe uma reconciliação nessa data.")

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

        cursor.execute("SELECT COUNT(*) FROM ajustes_saldo WHERE conta_id=%s", (conta_id,))
        if cursor.fetchone()[0] <= 1:
            raise HTTPException(status_code=400, detail="Uma conta precisa de pelo menos uma reconciliação.")

        cursor.execute("SELECT MIN(data) FROM ajustes_saldo WHERE conta_id=%s AND id != %s", (conta_id, ajuste_id))
        resto_row = cursor.fetchone()
        nova_mais_antiga = str(resto_row[0]) if resto_row and resto_row[0] else None

        primeiro_mov = primeiro_movimento_data(cursor, conta_id)
        if primeiro_mov and nova_mais_antiga and nova_mais_antiga > primeiro_mov:
            raise HTTPException(
                status_code=400,
                detail=f"Não é possível eliminar: esta conta tem movimentos a partir de {primeiro_mov}, e a reconciliação mais antiga que restaria é de {nova_mais_antiga}."
            )

        cursor.execute("DELETE FROM ajustes_saldo WHERE id=%s", (ajuste_id,))
        atualizar_saldo_atual(cursor, conta_id)
        conn.commit()
    finally:
        cursor.close()
        release_connection(conn)
    return {"ok": True}
