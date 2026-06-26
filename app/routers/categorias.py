from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import utilizador_atual
from app.db.database import get_connection
from app.schemas.categorias import CategoriaGestaoInput

router = APIRouter()


# ─── helpers internos ────────────────────────────────────────────────────────

def _pertence(cursor, categoria_id, uid):
    cursor.execute("SELECT id FROM categorias WHERE id=%s AND utilizador_id=%s", (categoria_id, uid))
    return cursor.fetchone() is not None


def _eliminar_grupo(cursor, categoria_id, migrar_para_id, forcar):
    cursor.execute("SELECT COUNT(*) FROM categorias WHERE parent_id=%s AND protegida", (categoria_id,))
    if cursor.fetchone()[0] > 0:
        raise HTTPException(
            status_code=400,
            detail="Este grupo contém uma categoria necessária para o sistema e não pode ser eliminado."
        )

    cursor.execute("SELECT COUNT(*) FROM categorias WHERE parent_id=%s", (categoria_id,))
    n = cursor.fetchone()[0]
    if n > 0 and not migrar_para_id and not forcar:
        raise HTTPException(status_code=400, detail=f"Este grupo tem {n} categoria(s). Escolhe um grupo de destino ou confirma a eliminação total.")

    if n > 0 and migrar_para_id:
        cursor.execute("UPDATE categorias SET parent_id=%s WHERE parent_id=%s", (migrar_para_id, categoria_id))
    elif n > 0 and forcar:
        cursor.execute("SELECT id FROM categorias WHERE parent_id=%s", (categoria_id,))
        for (fid,) in cursor.fetchall():
            cursor.execute("DELETE FROM movimentos WHERE categoria_id=%s", (fid,))
            cursor.execute("DELETE FROM categorias_aprendidas WHERE categoria_id=%s", (fid,))
        cursor.execute("DELETE FROM categorias WHERE parent_id=%s", (categoria_id,))

    cursor.execute("DELETE FROM categorias WHERE id=%s", (categoria_id,))


def _eliminar_folha(cursor, categoria_id, migrar_para_id, forcar):
    cursor.execute("SELECT COUNT(*) FROM movimentos WHERE categoria_id=%s", (categoria_id,))
    n = cursor.fetchone()[0]
    if n > 0 and not migrar_para_id and not forcar:
        raise HTTPException(status_code=400, detail=f"{n} transação(ões) usam esta categoria.")

    if n > 0 and migrar_para_id:
        cursor.execute("UPDATE movimentos SET categoria_id=%s WHERE categoria_id=%s", (migrar_para_id, categoria_id))
        cursor.execute("DELETE FROM categorias_aprendidas WHERE categoria_id=%s", (categoria_id,))
    elif n > 0 and forcar:
        cursor.execute("DELETE FROM movimentos WHERE categoria_id=%s", (categoria_id,))
        cursor.execute("DELETE FROM categorias_aprendidas WHERE categoria_id=%s", (categoria_id,))

    cursor.execute("DELETE FROM categorias WHERE id=%s", (categoria_id,))


# ─── rotas ───────────────────────────────────────────────────────────────────

@router.get("/categorias")
def listar_categorias(utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT c.id, c.nome, g.nome AS grupo, g.eh_recebimento
            FROM categorias c
            JOIN categorias g ON c.parent_id = g.id
            WHERE c.utilizador_id = %s
              AND NOT EXISTS (SELECT 1 FROM categorias f WHERE f.parent_id = c.id)
            ORDER BY g.eh_recebimento DESC, g.ordem, c.ordem
        """, (utilizador["sub"],))
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    return [{"id": r[0], "nome": r[1], "grupo": r[2], "eh_recebimento": r[3]} for r in rows]


@router.get("/categorias/arvore")
def arvore_categorias(utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]
    try:
        cursor.execute("""
            SELECT id, nome, eh_recebimento FROM categorias
            WHERE utilizador_id=%s AND parent_id IS NULL
            ORDER BY ordem
        """, (uid,))
        grupos = cursor.fetchall()

        cursor.execute("""
            SELECT id, nome, parent_id, protegida FROM categorias
            WHERE utilizador_id=%s AND parent_id IS NOT NULL
            ORDER BY ordem
        """, (uid,))
        categorias = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return [
        {
            "id": gid, "nome": nome, "eh_recebimento": eh_rec,
            "categorias": [{"id": c[0], "nome": c[1], "protegida": c[3]} for c in categorias if c[2] == gid]
        }
        for gid, nome, eh_rec in grupos
    ]


@router.post("/categorias")
def criar_categoria(dados: CategoriaGestaoInput, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]
    try:
        if dados.parent_id is None and dados.eh_recebimento is None:
            raise HTTPException(status_code=400, detail="Um grupo novo precisa de indicar se é Entrada ou Saída.")

        if dados.parent_id is not None and not _pertence(cursor, dados.parent_id, uid):
            raise HTTPException(status_code=404, detail="Grupo não encontrado")

        if dados.parent_id is None:
            cursor.execute("SELECT COALESCE(MAX(ordem),0)+1 FROM categorias WHERE utilizador_id=%s AND parent_id IS NULL", (uid,))
            eh_recebimento = dados.eh_recebimento
        else:
            cursor.execute("SELECT eh_recebimento FROM categorias WHERE id=%s", (dados.parent_id,))
            eh_recebimento = cursor.fetchone()[0]
            cursor.execute("SELECT COALESCE(MAX(ordem),0)+1 FROM categorias WHERE parent_id=%s", (dados.parent_id,))
        ordem = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO categorias (nome, parent_id, eh_recebimento, ordem, utilizador_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (dados.nome, dados.parent_id, eh_recebimento, ordem, uid))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return {"ok": True}


@router.put("/categorias/{categoria_id}")
def editar_categoria(categoria_id: int, dados: CategoriaGestaoInput, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]
    try:
        cursor.execute("SELECT parent_id, protegida FROM categorias WHERE id=%s AND utilizador_id=%s", (categoria_id, uid))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")
        parent_id, protegida = row

        if protegida:
            raise HTTPException(status_code=400, detail="Esta categoria é necessária para o sistema funcionar e não pode ser editada.")

        if dados.parent_id is not None:
            if parent_id is None:
                raise HTTPException(status_code=400, detail="Um grupo não pode ser movido para dentro de outro grupo.")
            if not _pertence(cursor, dados.parent_id, uid):
                raise HTTPException(status_code=404, detail="Grupo de destino não encontrado")
            cursor.execute("SELECT eh_recebimento FROM categorias WHERE id=%s", (dados.parent_id,))
            eh_recebimento = cursor.fetchone()[0]
            cursor.execute("""
                UPDATE categorias SET nome=%s, parent_id=%s, eh_recebimento=%s
                WHERE id=%s AND utilizador_id=%s
            """, (dados.nome, dados.parent_id, eh_recebimento, categoria_id, uid))
        else:
            cursor.execute("UPDATE categorias SET nome=%s WHERE id=%s AND utilizador_id=%s", (dados.nome, categoria_id, uid))

        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return {"ok": True}


@router.delete("/categorias/{categoria_id}")
def eliminar_categoria(categoria_id: int, migrar_para_id: int = None, forcar: bool = False, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]
    try:
        cursor.execute("SELECT parent_id, protegida FROM categorias WHERE id=%s AND utilizador_id=%s", (categoria_id, uid))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")
        parent_id, protegida = row

        if protegida:
            raise HTTPException(status_code=400, detail="Esta categoria é necessária para o sistema funcionar e não pode ser eliminada.")

        if migrar_para_id and not _pertence(cursor, migrar_para_id, uid):
            raise HTTPException(status_code=404, detail="Categoria de destino não encontrada")

        if parent_id is None:
            _eliminar_grupo(cursor, categoria_id, migrar_para_id, forcar)
        else:
            _eliminar_folha(cursor, categoria_id, migrar_para_id, forcar)

        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return {"ok": True}


@router.post("/categorias/{categoria_id}/mover")
def mover_categoria(categoria_id: int, direcao: str, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]
    try:
        cursor.execute("SELECT parent_id, ordem, eh_recebimento FROM categorias WHERE id=%s AND utilizador_id=%s", (categoria_id, uid))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")
        parent_id, ordem, eh_recebimento = row

        operador  = ">" if direcao == "down" else "<"
        ordenacao = "ASC" if direcao == "down" else "DESC"

        if parent_id is None:
            cursor.execute(f"""
                SELECT id, ordem FROM categorias
                WHERE utilizador_id=%s AND parent_id IS NULL AND eh_recebimento=%s AND ordem {operador} %s
                ORDER BY ordem {ordenacao} LIMIT 1
            """, (uid, eh_recebimento, ordem))
        else:
            cursor.execute(f"""
                SELECT id, ordem FROM categorias
                WHERE parent_id=%s AND ordem {operador} %s
                ORDER BY ordem {ordenacao} LIMIT 1
            """, (parent_id, ordem))
        vizinho = cursor.fetchone()

        if vizinho:
            vizinho_id, vizinho_ordem = vizinho
            cursor.execute("UPDATE categorias SET ordem=%s WHERE id=%s", (vizinho_ordem, categoria_id))
            cursor.execute("UPDATE categorias SET ordem=%s WHERE id=%s", (ordem, vizinho_id))
            conn.commit()
    finally:
        cursor.close()
        conn.close()
    return {"ok": True}
