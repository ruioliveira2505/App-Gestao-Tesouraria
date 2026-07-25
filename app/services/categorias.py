"""Regras de negócio de categorias — chamado pelo router, nunca o contrário.

Cada função recebe um cursor já aberto (a ligação/transacção é geridas pelo router) e
levanta ErroDominio para qualquer regra violada — não sabe o que é HTTP.
"""

from psycopg2.extras import RealDictCursor, execute_values

from app.core.dominio import ErroDominio
from app.schemas.categorias import CategoriaGestaoInput


def _eh_grupo(cursor: RealDictCursor, categoria_id: int, uid: str) -> bool:
    cursor.execute("SELECT id FROM categorias WHERE id=%s AND utilizador_id=%s AND parent_id IS NULL", (categoria_id, uid))
    return cursor.fetchone() is not None


def _eliminar_grupo(cursor: RealDictCursor, categoria_id: int, migrar_para_id: int | None, forcar: bool) -> None:
    """Elimina um grupo; migrar_para_id move as subcategorias, forcar apaga tudo."""
    cursor.execute("SELECT COUNT(*) AS n FROM categorias WHERE parent_id=%s AND protegida", (categoria_id,))
    if cursor.fetchone()["n"] > 0:
        raise ErroDominio(
            400, "GRUPO_TEM_CATEGORIA_PROTEGIDA",
            "Este grupo contém uma categoria necessária para o sistema e não pode ser eliminado."
        )

    cursor.execute("SELECT COUNT(*) AS n FROM categorias WHERE parent_id=%s", (categoria_id,))
    n = cursor.fetchone()["n"]
    if n > 0 and not migrar_para_id and not forcar:
        raise ErroDominio(
            400, "GRUPO_COM_CATEGORIAS",
            f"Este grupo tem {n} categoria(s). Escolhe um grupo de destino ou confirma a eliminação total.",
            ctx={"n": n},
        )

    if n > 0 and migrar_para_id:
        cursor.execute("UPDATE categorias SET parent_id=%s WHERE parent_id=%s", (migrar_para_id, categoria_id))
    # com forcar=true não é preciso apagar nada à parte — subcategorias, movimentos e
    # categorias_aprendidas caem todos em ON DELETE CASCADE a partir daqui

    cursor.execute("DELETE FROM categorias WHERE id=%s", (categoria_id,))


def _eliminar_folha(cursor: RealDictCursor, categoria_id: int, migrar_para_id: int | None, forcar: bool) -> None:
    """Elimina uma categoria-folha; migrar_para_id reatribui os movimentos, forcar
    apaga-os (movimentos e a cache de categorização caem em ON DELETE CASCADE)."""
    cursor.execute("SELECT COUNT(*) AS n FROM movimentos WHERE categoria_id=%s", (categoria_id,))
    n = cursor.fetchone()["n"]
    if n > 0 and not migrar_para_id and not forcar:
        raise ErroDominio(400, "CATEGORIA_COM_MOVIMENTOS", f"{n} transação(ões) usam esta categoria.", ctx={"n": n})

    if n > 0 and migrar_para_id:
        cursor.execute("UPDATE movimentos SET categoria_id=%s WHERE categoria_id=%s", (migrar_para_id, categoria_id))

    cursor.execute("DELETE FROM categorias WHERE id=%s", (categoria_id,))


def listar_categorias(cursor: RealDictCursor, uid: str) -> list[dict]:
    """Lista só as categorias-folha, cada uma com o nome do grupo a que pertence."""
    cursor.execute("""
        SELECT c.id, c.nome, g.nome AS grupo, g.eh_recebimento, c.slug
        FROM categorias c
        JOIN categorias g ON c.parent_id = g.id
        WHERE c.utilizador_id = %s
          AND NOT EXISTS (SELECT 1 FROM categorias f WHERE f.parent_id = c.id)
        ORDER BY g.eh_recebimento DESC, g.ordem, c.ordem
    """, (uid,))
    rows = cursor.fetchall()
    return [
        {"id": r["id"], "nome": r["nome"], "grupo": r["grupo"], "eh_recebimento": r["eh_recebimento"], "slug": r["slug"]}
        for r in rows
    ]


def listar_arvore(cursor: RealDictCursor, uid: str) -> list[dict]:
    """Grupos com as respectivas categorias-folha aninhadas — usado nos selectores da UI."""
    cursor.execute("""
        SELECT id, nome, eh_recebimento, slug FROM categorias
        WHERE utilizador_id=%s AND parent_id IS NULL
        ORDER BY ordem
    """, (uid,))
    grupos = cursor.fetchall()

    cursor.execute("""
        SELECT id, nome, parent_id, protegida, slug FROM categorias
        WHERE utilizador_id=%s AND parent_id IS NOT NULL
        ORDER BY ordem
    """, (uid,))
    categorias = cursor.fetchall()

    return [
        {
            "id": g["id"], "nome": g["nome"], "eh_recebimento": g["eh_recebimento"], "slug": g["slug"],
            "categorias": [
                {"id": c["id"], "nome": c["nome"], "protegida": c["protegida"], "slug": c["slug"]}
                for c in categorias if c["parent_id"] == g["id"]
            ]
        }
        for g in grupos
    ]


def criar_categoria(cursor: RealDictCursor, uid: str, dados: CategoriaGestaoInput) -> None:
    """Cria um grupo (sem parent_id, com eh_recebimento) ou uma categoria-folha (com
    parent_id — herda a direcção do grupo)."""
    if dados.parent_id is None and dados.eh_recebimento is None:
        raise ErroDominio(400, "DIRECAO_EM_FALTA", "Um grupo novo precisa de indicar se é Entrada ou Saída.")

    if dados.parent_id is not None and not _eh_grupo(cursor, dados.parent_id, uid):
        raise ErroDominio(404, "GRUPO_NAO_ENCONTRADO", "Grupo não encontrado")

    if dados.parent_id is None:
        cursor.execute("SELECT COALESCE(MAX(ordem),0)+1 AS ordem FROM categorias WHERE utilizador_id=%s AND parent_id IS NULL", (uid,))
        eh_recebimento = dados.eh_recebimento
    else:
        cursor.execute("SELECT eh_recebimento FROM categorias WHERE id=%s", (dados.parent_id,))
        eh_recebimento = cursor.fetchone()["eh_recebimento"]
        cursor.execute("SELECT COALESCE(MAX(ordem),0)+1 AS ordem FROM categorias WHERE parent_id=%s", (dados.parent_id,))
    ordem = cursor.fetchone()["ordem"]

    cursor.execute("""
        INSERT INTO categorias (nome, parent_id, eh_recebimento, ordem, utilizador_id)
        VALUES (%s, %s, %s, %s, %s)
    """, (dados.nome, dados.parent_id, eh_recebimento, ordem, uid))


def reordenar(cursor: RealDictCursor, uid: str, ids: list[int]) -> None:
    """Grava a ordem (a lista de ids, pela nova ordem) — usado no arrastar-e-largar. Uma
    única query (UPDATE ... FROM VALUES) em vez de um UPDATE por id."""
    valores = [(categoria_id, posicao, uid) for posicao, categoria_id in enumerate(ids)]
    execute_values(
        cursor,
        """
        UPDATE categorias AS c SET ordem = v.ordem
        FROM (VALUES %s) AS v(id, ordem, uid)
        WHERE c.id = v.id AND c.utilizador_id = v.uid::integer
        """,
        valores,
    )


def editar_categoria(cursor: RealDictCursor, uid: str, categoria_id: int, dados: CategoriaGestaoInput) -> None:
    """Renomeia e/ou move uma categoria-folha para outro grupo; categorias protegidas
    não podem ser editadas, e um grupo não pode ser movido para dentro de outro grupo."""
    cursor.execute("SELECT parent_id, protegida FROM categorias WHERE id=%s AND utilizador_id=%s", (categoria_id, uid))
    row = cursor.fetchone()
    if not row:
        raise ErroDominio(404, "CATEGORIA_NAO_ENCONTRADA", "Categoria não encontrada")
    parent_id, protegida = row["parent_id"], row["protegida"]

    if protegida:
        raise ErroDominio(400, "CATEGORIA_PROTEGIDA", "Esta categoria é necessária para o sistema funcionar e não pode ser editada.")

    if dados.parent_id is not None:
        if parent_id is None:
            raise ErroDominio(400, "GRUPO_NAO_PODE_SER_SUBCATEGORIA", "Um grupo não pode ser movido para dentro de outro grupo.")
        if not _eh_grupo(cursor, dados.parent_id, uid):
            raise ErroDominio(404, "GRUPO_DESTINO_NAO_ENCONTRADO", "Grupo de destino não encontrado")
        cursor.execute("SELECT eh_recebimento FROM categorias WHERE id=%s", (dados.parent_id,))
        eh_recebimento = cursor.fetchone()["eh_recebimento"]
        cursor.execute("""
            UPDATE categorias SET nome=%s, parent_id=%s, eh_recebimento=%s
            WHERE id=%s AND utilizador_id=%s
        """, (dados.nome, dados.parent_id, eh_recebimento, categoria_id, uid))
    else:
        cursor.execute("UPDATE categorias SET nome=%s WHERE id=%s AND utilizador_id=%s", (dados.nome, categoria_id, uid))


def eliminar_categoria(cursor: RealDictCursor, uid: str, categoria_id: int, migrar_para_id: int | None, forcar: bool) -> None:
    """Elimina um grupo ou categoria-folha; migrar_para_id/forcar tratam do que fazer aos
    movimentos (ou subcategorias, no caso de um grupo) que ainda lá estejam."""
    cursor.execute("SELECT parent_id, protegida, eh_recebimento FROM categorias WHERE id=%s AND utilizador_id=%s", (categoria_id, uid))
    row = cursor.fetchone()
    if not row:
        raise ErroDominio(404, "CATEGORIA_NAO_ENCONTRADA", "Categoria não encontrada")
    parent_id, protegida, eh_recebimento = row["parent_id"], row["protegida"], row["eh_recebimento"]

    if protegida:
        raise ErroDominio(400, "CATEGORIA_PROTEGIDA", "Esta categoria é necessária para o sistema funcionar e não pode ser eliminada.")

    if migrar_para_id:
        cursor.execute("SELECT parent_id, eh_recebimento FROM categorias WHERE id=%s AND utilizador_id=%s", (migrar_para_id, uid))
        destino = cursor.fetchone()
        if not destino:
            raise ErroDominio(404, "CATEGORIA_DESTINO_NAO_ENCONTRADA", "Categoria de destino não encontrada")
        destino_parent_id, destino_eh_recebimento = destino["parent_id"], destino["eh_recebimento"]

        if (parent_id is None) != (destino_parent_id is None):
            raise ErroDominio(400, "DESTINO_TIPO_INCOMPATIVEL", "O destino tem de ser do mesmo tipo (grupo ou categoria).")
        if destino_eh_recebimento != eh_recebimento:
            raise ErroDominio(400, "DESTINO_DIRECAO_INCOMPATIVEL", "O destino tem de ser da mesma direção (Entrada ou Saída).")

    if parent_id is None:
        _eliminar_grupo(cursor, categoria_id, migrar_para_id, forcar)
    else:
        _eliminar_folha(cursor, categoria_id, migrar_para_id, forcar)
