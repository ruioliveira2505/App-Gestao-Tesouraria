import uuid
from fastapi import APIRouter, Depends, HTTPException

from app.db.database import get_connection
from app.core.deps import utilizador_atual
from app.services.reconciliacoes import reconciliacao_mais_antiga_data
from app.services.categorizacao import guardar_em_cache
from app.schemas.movimentos import MovimentoInput

router = APIRouter()


def _validar_data_movimento(cursor, conta_id, data, acao):
    rec = reconciliacao_mais_antiga_data(cursor, conta_id)
    if rec and data < rec:
        raise HTTPException(
            status_code=400,
            detail=f"Esta conta só tem reconciliações a partir de {rec}. Cria uma reconciliação anterior a {data} antes de {acao}."
        )


def _validar_categoria_direcao(cursor, categoria_id, valor, uid):
    cursor.execute("SELECT eh_recebimento FROM categorias WHERE id=%s AND utilizador_id=%s", (categoria_id, uid))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    if (valor > 0) != row[0]:
        direcao = "uma categoria de Entrada" if valor > 0 else "uma categoria de Saída"
        raise HTTPException(status_code=400, detail=f"Este movimento precisa de {direcao}.")


@router.get("/movimentos")
def listar_movimentos(
    utilizador: dict = Depends(utilizador_atual),
    conta_id: str = None,
    categoria_id: int = None,
    direcao: str = None,
    data_de: str = None,
    data_ate: str = None,
    precisa_confirmacao: bool = None,
):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]

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

    try:
        cursor.execute("""
            SELECT m.id, m.conta_id, m.data, m.descricao, m.valor,
                   m.categoria_id, c.nome, g.nome, m.origem_cat, c.protegida
            FROM movimentos m
            JOIN categorias c ON m.categoria_id = c.id
            JOIN categorias g ON c.parent_id = g.id
            WHERE m.utilizador_id = %s
              AND (%s IS NULL OR m.conta_id = %s)
              AND (%s IS NULL OR m.categoria_id = %s)
              AND (%s IS NULL OR m.data >= %s)
              AND (%s IS NULL OR m.data <= %s)
        """ + filtro_direcao + filtro_confirmacao + """
            ORDER BY m.data DESC, m.criado_em DESC
        """, [uid, conta_id, conta_id, categoria_id, categoria_id, data_de, data_de, data_ate, data_ate])
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return [
        {
            "id": r[0], "conta_id": r[1], "data": str(r[2]), "descricao": r[3], "valor": float(r[4]),
            "categoria_id": r[5], "categoria": r[6], "grupo": r[7], "origem_cat": r[8],
            "confirmado": r[8] in ("manual", "cache"),
            "sem_categoria": r[9],
        }
        for r in rows
    ]


@router.get("/movimentos/pendentes/contagem")
def contar_movimentos_pendentes(utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM movimentos
            WHERE utilizador_id = %s AND origem_cat IN ('llm', 'sem_match')
        """, (utilizador["sub"],))
        contagem = cursor.fetchone()[0]
    finally:
        cursor.close()
        conn.close()
    return {"contagem": contagem}


@router.post("/movimentos")
def criar_movimento(dados: MovimentoInput, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]
    try:
        _validar_categoria_direcao(cursor, dados.categoria_id, dados.valor, uid)
        _validar_data_movimento(cursor, dados.conta_id, dados.data, "adicionar este movimento")
        cursor.execute("""
            INSERT INTO movimentos (id, conta_id, data, descricao, valor, categoria_id, origem_cat, utilizador_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (str(uuid.uuid4()), dados.conta_id, dados.data, dados.descricao, dados.valor, dados.categoria_id, "manual", uid))
        conn.commit()
        guardar_em_cache(conn, dados.descricao, dados.categoria_id, uid, confirmado=True)
    finally:
        cursor.close()
        conn.close()
    return {"ok": True}


@router.put("/movimentos/{movimento_id}")
def editar_movimento(movimento_id: str, dados: MovimentoInput, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]
    try:
        _validar_categoria_direcao(cursor, dados.categoria_id, dados.valor, uid)
        _validar_data_movimento(cursor, dados.conta_id, dados.data, "mover este movimento para essa data")
        cursor.execute("""
            UPDATE movimentos
            SET conta_id=%s, data=%s, descricao=%s, valor=%s, categoria_id=%s, origem_cat='manual'
            WHERE id=%s AND utilizador_id=%s
        """, (dados.conta_id, dados.data, dados.descricao, dados.valor, dados.categoria_id, movimento_id, uid))
        conn.commit()
        guardar_em_cache(conn, dados.descricao, dados.categoria_id, uid, confirmado=True)
    finally:
        cursor.close()
        conn.close()
    return {"ok": True}


@router.delete("/movimentos/{movimento_id}")
def eliminar_movimento(movimento_id: str, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM movimentos WHERE id = %s AND utilizador_id = %s",
            (movimento_id, utilizador["sub"])
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return {"ok": True}


@router.post("/movimentos/{movimento_id}/confirmar")
def confirmar_movimento(movimento_id: str, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]
    try:
        cursor.execute(
            "SELECT descricao, categoria_id FROM movimentos WHERE id=%s AND utilizador_id=%s",
            (movimento_id, uid)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Movimento não encontrado")
        descricao, categoria_id = row

        cursor.execute("UPDATE movimentos SET origem_cat='manual' WHERE id=%s", (movimento_id,))
        conn.commit()
        guardar_em_cache(conn, descricao, categoria_id, uid, confirmado=True)
    finally:
        cursor.close()
        conn.close()
    return {"ok": True}


@router.post("/movimentos/confirmar-todos")
def confirmar_todos_os_pendentes(utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]
    try:
        cursor.execute("""
            SELECT DISTINCT descricao, categoria_id FROM movimentos
            WHERE utilizador_id=%s AND origem_cat IN ('llm', 'sem_match')
        """, (uid,))
        pendentes = cursor.fetchall()

        cursor.execute("""
            UPDATE movimentos SET origem_cat='manual'
            WHERE utilizador_id=%s AND origem_cat IN ('llm', 'sem_match')
        """, (uid,))
        conn.commit()

        for descricao, categoria_id in pendentes:
            guardar_em_cache(conn, descricao, categoria_id, uid, confirmado=True)
    finally:
        cursor.close()
        conn.close()
    return {"ok": True, "confirmados": len(pendentes)}
