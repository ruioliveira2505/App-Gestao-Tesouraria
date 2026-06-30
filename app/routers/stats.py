from collections import defaultdict
from datetime import timedelta

from fastapi import APIRouter, Depends

from app.core.deps import utilizador_atual
from app.db.database import get_connection, release_connection, release_connection

router = APIRouter()


@router.get("/stats/mensal")
def stats_mensal(utilizador: dict = Depends(utilizador_atual), conta_id: str = None, tipo: str = None, data_de: str = None, data_ate: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]
    try:
        cursor.execute("""
            SELECT
                TO_CHAR(DATE_TRUNC('month', m.data), 'YYYY-MM') AS mes,
                SUM(CASE WHEN m.valor > 0 THEN m.valor ELSE 0 END) AS entradas,
                SUM(CASE WHEN m.valor < 0 THEN ABS(m.valor) ELSE 0 END) AS saidas
            FROM movimentos m
            JOIN contas ct ON m.conta_id = ct.id
            WHERE m.utilizador_id = %s
              AND (%s IS NULL OR m.conta_id = %s)
              AND (%s IS NULL OR ct.tipo = %s)
              AND (%s IS NULL OR m.data >= %s)
              AND (%s IS NULL OR m.data <= %s)
            GROUP BY DATE_TRUNC('month', m.data)
            ORDER BY DATE_TRUNC('month', m.data)
        """, [uid, conta_id, conta_id, tipo, tipo, data_de, data_de, data_ate, data_ate])
        rows = cursor.fetchall()
    finally:
        cursor.close()
        release_connection(conn)

    return [
        {"mes": r[0], "entradas": float(r[1]), "saidas": float(r[2]), "liquido": float(r[1]) - float(r[2])}
        for r in rows
    ]


@router.get("/stats/categorias")
def stats_categorias(utilizador: dict = Depends(utilizador_atual), conta_id: str = None, tipo: str = None, data_de: str = None, data_ate: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]
    try:
        cursor.execute("""
            WITH RECURSIVE arvore AS (
                SELECT id, parent_id, nome AS caminho, nome AS grupo_raiz, eh_recebimento
                FROM categorias
                WHERE utilizador_id = %s AND parent_id IS NULL
                UNION ALL
                SELECT c.id, c.parent_id,
                       a.caminho || ' > ' || c.nome,
                       a.grupo_raiz, a.eh_recebimento
                FROM categorias c
                JOIN arvore a ON c.parent_id = a.id
            )
            SELECT a.grupo_raiz, a.caminho, a.eh_recebimento,
                   COUNT(*) AS n, SUM(ABS(m.valor)) AS total
            FROM movimentos m
            JOIN contas ct ON m.conta_id = ct.id
            JOIN arvore a ON m.categoria_id = a.id
            WHERE m.utilizador_id = %s
              AND (%s IS NULL OR m.conta_id = %s)
              AND (%s IS NULL OR ct.tipo = %s)
              AND (%s IS NULL OR m.data >= %s)
              AND (%s IS NULL OR m.data <= %s)
              AND NOT EXISTS (SELECT 1 FROM categorias f WHERE f.parent_id = a.id)
            GROUP BY a.grupo_raiz, a.caminho, a.eh_recebimento
            ORDER BY a.eh_recebimento DESC, total DESC
        """, [uid, uid, conta_id, conta_id, tipo, tipo, data_de, data_de, data_ate, data_ate])
        rows = cursor.fetchall()
    finally:
        cursor.close()
        release_connection(conn)

    total_out = sum(float(r[4]) for r in rows if not r[2])
    total_in  = sum(float(r[4]) for r in rows if r[2])

    return [
        {
            "grupo": r[0], "categoria": r[1], "eh_recebimento": r[2], "n": r[3],
            "total": float(r[4]),
            "percentagem": round(float(r[4]) / (total_in if r[2] else total_out) * 100, 1) if (total_in if r[2] else total_out) else 0,
        }
        for r in rows
    ]


@router.get("/stats/grupos")
def stats_grupos(utilizador: dict = Depends(utilizador_atual), conta_id: str = None, tipo: str = None, data_de: str = None, data_ate: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]
    try:
        cursor.execute("""
            WITH RECURSIVE arvore AS (
                SELECT id, parent_id, nome, nome AS grupo_raiz, eh_recebimento, 0 AS nivel
                FROM categorias
                WHERE utilizador_id = %s AND parent_id IS NULL
                UNION ALL
                SELECT c.id, c.parent_id, c.nome, a.grupo_raiz, a.eh_recebimento, a.nivel + 1
                FROM categorias c
                JOIN arvore a ON c.parent_id = a.id
            )
            SELECT a.grupo_raiz, a.eh_recebimento, a.nome AS categoria,
                   a.nivel, COUNT(*) AS n, SUM(ABS(m.valor)) AS total
            FROM movimentos m
            JOIN contas ct ON m.conta_id = ct.id
            JOIN arvore a ON m.categoria_id = a.id
            WHERE m.utilizador_id = %s
              AND (%s IS NULL OR m.conta_id = %s)
              AND (%s IS NULL OR ct.tipo = %s)
              AND (%s IS NULL OR m.data >= %s)
              AND (%s IS NULL OR m.data <= %s)
              AND NOT EXISTS (SELECT 1 FROM categorias f WHERE f.parent_id = a.id)
            GROUP BY a.grupo_raiz, a.eh_recebimento, a.nome, a.nivel
            ORDER BY a.eh_recebimento DESC, a.grupo_raiz, total DESC
        """, [uid, uid, conta_id, conta_id, tipo, tipo, data_de, data_de, data_ate, data_ate])
        rows = cursor.fetchall()
    finally:
        cursor.close()
        release_connection(conn)

    grupos = defaultdict(lambda: {"eh_recebimento": None, "total": 0.0, "subcategorias": []})
    for r in rows:
        grupos[r[0]]["eh_recebimento"] = r[1]
        grupos[r[0]]["total"] += float(r[5])
        grupos[r[0]]["subcategorias"].append({"categoria": r[2], "total": float(r[5]), "n": r[4]})

    return [
        {
            "grupo": grupo, "eh_recebimento": dados["eh_recebimento"],
            "total": round(dados["total"], 2),
            "subcategorias": sorted(dados["subcategorias"], key=lambda x: x["total"], reverse=True),
        }
        for grupo, dados in sorted(grupos.items(), key=lambda x: (not x[1]["eh_recebimento"], -x[1]["total"]))
    ]


@router.get("/stats/saldo-diario")
def stats_saldo_diario(utilizador: dict = Depends(utilizador_atual), conta_id: str = None, tipo: str = None, data_de: str = None, data_ate: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]
    try:
        cursor.execute("""
            WITH contas_filtradas AS (
                SELECT id FROM contas
                WHERE utilizador_id = %s
                  AND (%s IS NULL OR id = %s)
                  AND (%s IS NULL OR tipo = %s)
            ),
            dias AS (
                SELECT generate_series(
                    (SELECT MIN(data) FROM ajustes_saldo WHERE conta_id IN (SELECT id FROM contas_filtradas)),
                    CURRENT_DATE, '1 day'::interval
                )::date AS dia
            ),
            saldo_por_conta_dia AS (
                SELECT d.dia, cf.id AS conta_id,
                       a.saldo_real + COALESCE((
                           SELECT SUM(m.valor) FROM movimentos m
                           WHERE m.conta_id = cf.id AND m.data >= a.data AND m.data <= d.dia
                       ), 0) AS saldo
                FROM dias d
                CROSS JOIN contas_filtradas cf
                CROSS JOIN LATERAL (
                    SELECT saldo_real, data FROM ajustes_saldo
                    WHERE conta_id = cf.id AND data <= d.dia
                    ORDER BY data DESC LIMIT 1
                ) a
            )
            SELECT dia, SUM(saldo) AS saldo
            FROM saldo_por_conta_dia
            GROUP BY dia
            ORDER BY dia
        """, [uid, conta_id, conta_id, tipo, tipo])
        rows = cursor.fetchall()
    finally:
        cursor.close()
        release_connection(conn)

    if not rows:
        return []

    pontos = [{"data": str(r[0]), "saldo": round(float(r[1]), 2)} for r in rows]
    if data_de:
        pontos = [p for p in pontos if p["data"] >= data_de]
    if data_ate:
        pontos = [p for p in pontos if p["data"] <= data_ate]
    return pontos


@router.get("/stats/recorrentes")
def stats_recorrentes(utilizador: dict = Depends(utilizador_atual), conta_id: str = None, tipo: str = None, data_de: str = None, data_ate: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]
    try:
        cursor.execute("""
            SELECT m.descricao, c.nome AS categoria, g.nome AS grupo, m.data, m.valor
            FROM movimentos m
            JOIN categorias c ON m.categoria_id = c.id
            JOIN categorias g ON c.parent_id = g.id
            JOIN contas ct ON m.conta_id = ct.id
            WHERE m.utilizador_id = %s AND m.valor < 0
              AND (%s IS NULL OR m.conta_id = %s)
              AND (%s IS NULL OR ct.tipo = %s)
              AND (%s IS NULL OR m.data >= %s)
              AND (%s IS NULL OR m.data <= %s)
            ORDER BY m.descricao, c.nome, m.data
        """, [uid, conta_id, conta_id, tipo, tipo, data_de, data_de, data_ate, data_ate])
        rows = cursor.fetchall()
    finally:
        cursor.close()
        release_connection(conn)

    grupos = defaultdict(list)
    for descricao, categoria, grupo, data_mov, valor in rows:
        grupos[(descricao, categoria, grupo)].append((data_mov, float(valor)))

    resultado = []
    for (descricao, categoria, grupo), ocorrencias in grupos.items():
        if len(ocorrencias) < 2:
            continue

        datas = [o[0] for o in ocorrencias]
        valores = [o[1] for o in ocorrencias]
        intervalos = [(datas[i] - datas[i-1]).days for i in range(1, len(datas))]

        intervalo_medio = sum(intervalos) / len(intervalos)
        if intervalo_medio == 0:
            continue

        desvio = (sum((i - intervalo_medio) ** 2 for i in intervalos) / len(intervalos)) ** 0.5
        regular = (desvio / intervalo_medio) < 0.4
        proxima_data = datas[-1] + timedelta(days=round(intervalo_medio))

        resultado.append({
            "descricao": descricao,
            "categoria": categoria,
            "grupo": grupo,
            "ocorrencias": len(ocorrencias),
            "valor_medio": round(sum(valores) / len(valores), 2),
            "ultima_vez": str(datas[-1]),
            "intervalo_medio_dias": round(intervalo_medio),
            "proxima_data_estimada": str(proxima_data),
            "regular": regular,
        })

    resultado.sort(key=lambda x: (not x["regular"], -x["ocorrencias"]))
    return resultado