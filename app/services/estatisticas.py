"""Regras de negócio de estatísticas e agregações sobre movimentos — tudo somente-leitura.

Cada função recebe um cursor já aberto (a ligação/transacção é gerida pelo router) e
levanta ErroDominio para qualquer regra violada — não sabe o que é HTTP.

Filtros comuns à maioria das funções: conta_id/tipo/data_de/data_ate (listas separadas
por vírgula onde aplicável) e excluir_categorias (ids a ignorar).
"""

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from psycopg2.extras import RealDictCursor

from app.core.dominio import ErroDominio
from app.core.utils import lista_sql
from app.services.contas import PONTOS_SALDO_CTE


def _excluir_sql(excluir_categorias: str | None) -> tuple[str, list[int]]:
    """Fragmento SQL "AND categoria_id NOT IN (...)" a partir de uma lista CSV de ids."""
    if not excluir_categorias:
        return "", []
    try:
        ids = [int(x) for x in excluir_categorias.split(',') if x.strip()]
    except ValueError:
        raise ErroDominio(400, "EXCLUIR_CATEGORIAS_INVALIDO", "excluir_categorias tem de ser uma lista de ids separados por vírgula.") from None
    if not ids:
        return "", []
    placeholders = ','.join(['%s'] * len(ids))
    return f"AND m.categoria_id NOT IN ({placeholders})", ids


def stats_mensal(
    cursor: RealDictCursor, uid: str, conta_id: str | None, tipo: str | None,
    data_de: str | None, data_ate: str | None, excluir_categorias: str | None,
) -> list[dict]:
    """Entradas/saídas/líquido agregados por mês."""
    conta_cond, conta_vals = lista_sql("m.conta_id", conta_id)
    tipo_cond, tipo_vals = lista_sql("ct.tipo", tipo)
    excluir_cond, excluir_ids = _excluir_sql(excluir_categorias)

    cursor.execute("""
        SELECT
            TO_CHAR(DATE_TRUNC('month', m.data), 'YYYY-MM') AS mes,
            SUM(CASE WHEN m.valor > 0 THEN m.valor ELSE 0 END) AS entradas,
            SUM(CASE WHEN m.valor < 0 THEN ABS(m.valor) ELSE 0 END) AS saidas
        FROM movimentos m
        JOIN contas ct ON m.conta_id = ct.id
        WHERE m.utilizador_id = %s
          AND (%s IS NULL OR m.data >= %s)
          AND (%s IS NULL OR m.data <= %s)
    """ + conta_cond + tipo_cond + excluir_cond + """
        GROUP BY DATE_TRUNC('month', m.data)
        ORDER BY DATE_TRUNC('month', m.data)
    """, [uid, data_de, data_de, data_ate, data_ate, *conta_vals, *tipo_vals, *excluir_ids])
    rows = cursor.fetchall()

    return [
        # subtracção feita em Decimal (o tipo que o psycopg2 devolve para numeric) antes
        # de converter para float — evita somar o erro de arredondamento de dois floats
        # em vez de um só; ver analise-tesouraria.md, secção "Modelo de dados/Migrações".
        {"mes": r["mes"], "entradas": float(r["entradas"]), "saidas": float(r["saidas"]),
         "liquido": float(r["entradas"] - r["saidas"])}
        for r in rows
    ]


def stats_grupos(
    cursor: RealDictCursor, uid: str, conta_id: str | None, tipo: str | None,
    data_de: str | None, data_ate: str | None, excluir_categorias: str | None,
) -> list[dict]:
    """Total por grupo, com as categorias-folha de cada grupo listadas dentro dele."""
    conta_cond, conta_vals = lista_sql("m.conta_id", conta_id)
    tipo_cond, tipo_vals = lista_sql("ct.tipo", tipo)
    excluir_cond, excluir_ids = _excluir_sql(excluir_categorias)

    cursor.execute("""
        WITH RECURSIVE arvore AS (
            SELECT id, parent_id, nome, slug, nome AS grupo_raiz, id AS grupo_raiz_id,
                   slug AS grupo_raiz_slug, eh_recebimento, 0 AS nivel
            FROM categorias
            WHERE utilizador_id = %s AND parent_id IS NULL
            UNION ALL
            SELECT c.id, c.parent_id, c.nome, c.slug, a.grupo_raiz, a.grupo_raiz_id,
                   a.grupo_raiz_slug, a.eh_recebimento, a.nivel + 1
            FROM categorias c
            JOIN arvore a ON c.parent_id = a.id
        )
        SELECT a.grupo_raiz, a.grupo_raiz_id, a.grupo_raiz_slug, a.eh_recebimento,
               a.nome AS categoria, a.id AS categoria_id, a.slug AS categoria_slug,
               a.nivel, COUNT(*) AS n, SUM(ABS(m.valor)) AS total
        FROM movimentos m
        JOIN contas ct ON m.conta_id = ct.id
        JOIN arvore a ON m.categoria_id = a.id
        WHERE m.utilizador_id = %s
          AND (%s IS NULL OR m.data >= %s)
          AND (%s IS NULL OR m.data <= %s)
          AND NOT EXISTS (SELECT 1 FROM categorias f WHERE f.parent_id = a.id)
    """ + conta_cond + tipo_cond + excluir_cond + """
        GROUP BY a.grupo_raiz, a.grupo_raiz_id, a.grupo_raiz_slug, a.eh_recebimento, a.nome, a.id, a.slug, a.nivel
        ORDER BY a.eh_recebimento DESC, a.grupo_raiz, total DESC
    """, [uid, uid, data_de, data_de, data_ate, data_ate, *conta_vals, *tipo_vals, *excluir_ids])  # noqa: S608
    rows = cursor.fetchall()

    # total acumulado em Decimal (o tipo que o psycopg2 devolve para numeric) — soma exacta
    # de todas as subcategorias do grupo antes de arredondar/converter para float uma única
    # vez, em vez de ir arredondando um float a cada iteração do ciclo.
    grupos = defaultdict(lambda: {"nome": None, "slug": None, "eh_recebimento": None, "grupo_id": None, "total": Decimal("0"), "subcategorias": []})
    for r in rows:
        chave = r["grupo_raiz_id"]
        grupos[chave]["nome"] = r["grupo_raiz"]
        grupos[chave]["slug"] = r["grupo_raiz_slug"]
        grupos[chave]["eh_recebimento"] = r["eh_recebimento"]
        grupos[chave]["grupo_id"] = r["grupo_raiz_id"]
        grupos[chave]["total"] += r["total"]
        grupos[chave]["subcategorias"].append({
            "categoria": r["categoria"], "categoria_id": r["categoria_id"], "categoria_slug": r["categoria_slug"],
            "total": float(r["total"]), "n": r["n"]
        })

    return [
        {
            "grupo": dados["nome"], "grupo_id": dados["grupo_id"], "grupo_slug": dados["slug"],
            "eh_recebimento": dados["eh_recebimento"],
            "total": round(float(dados["total"]), 2),
            "subcategorias": sorted(dados["subcategorias"], key=lambda x: x["total"], reverse=True),
        }
        for chave, dados in sorted(grupos.items(), key=lambda x: (not x[1]["eh_recebimento"], -x[1]["total"]))
    ]


def stats_mensal_detalhe(
    cursor: RealDictCursor, uid: str, grupo_id: int | None, categoria_id: int | None,
    conta_id: str | None, tipo: str | None, data_de: str | None, data_ate: str | None,
    excluir_categorias: str | None,
) -> list[dict] | dict:
    """Evolução mensal de uma categoria (lista mes+total), ou de um grupo (objecto
    meses+categorias, com as categorias separadas) — a forma da resposta depende de qual
    parâmetro é passado. grupo_id e categoria_id são mutuamente exclusivos."""
    if not grupo_id and not categoria_id:
        raise ErroDominio(400, "PARAMETRO_EM_FALTA", "Indica grupo_id ou categoria_id.")
    if grupo_id and categoria_id:
        raise ErroDominio(400, "PARAMETROS_EXCLUSIVOS", "Indica apenas grupo_id ou apenas categoria_id, não os dois.")

    conta_cond, conta_vals = lista_sql("m.conta_id", conta_id)
    tipo_cond, tipo_vals = lista_sql("ct.tipo", tipo)
    excluir_cond, excluir_ids = _excluir_sql(excluir_categorias)

    if categoria_id:
        cursor.execute(
            "SELECT id FROM categorias WHERE id=%s AND utilizador_id=%s",
            (categoria_id, uid)
        )
        if not cursor.fetchone():
            raise ErroDominio(404, "CATEGORIA_NAO_ENCONTRADA", "Categoria não encontrada")

        cursor.execute("""
            SELECT TO_CHAR(DATE_TRUNC('month', m.data), 'YYYY-MM') AS mes,
                   SUM(ABS(m.valor)) AS total
            FROM movimentos m
            JOIN contas ct ON m.conta_id = ct.id
            WHERE m.utilizador_id = %s
              AND m.categoria_id = %s
              AND (%s IS NULL OR m.data >= %s)
              AND (%s IS NULL OR m.data <= %s)
        """ + conta_cond + tipo_cond + excluir_cond + """
            GROUP BY DATE_TRUNC('month', m.data)
            ORDER BY DATE_TRUNC('month', m.data)
        """, [uid, categoria_id, data_de, data_de, data_ate, data_ate, *conta_vals, *tipo_vals, *excluir_ids])  # noqa: S608
        rows = cursor.fetchall()
        return [{"mes": r["mes"], "total": float(r["total"])} for r in rows]

    cursor.execute(
        "SELECT id FROM categorias WHERE id=%s AND utilizador_id=%s AND parent_id IS NULL",
        (grupo_id, uid)
    )
    if not cursor.fetchone():
        raise ErroDominio(404, "GRUPO_NAO_ENCONTRADO", "Grupo não encontrado")

    cursor.execute("""
        SELECT TO_CHAR(DATE_TRUNC('month', m.data), 'YYYY-MM') AS mes,
               c.nome AS categoria, c.slug AS categoria_slug,
               SUM(ABS(m.valor)) AS total
        FROM movimentos m
        JOIN contas ct ON m.conta_id = ct.id
        JOIN categorias c ON m.categoria_id = c.id
        WHERE m.utilizador_id = %s
          AND c.parent_id = %s
          AND (%s IS NULL OR m.data >= %s)
          AND (%s IS NULL OR m.data <= %s)
    """ + conta_cond + tipo_cond + excluir_cond + """
        GROUP BY DATE_TRUNC('month', m.data), c.nome, c.slug
        ORDER BY DATE_TRUNC('month', m.data), c.nome
    """, [uid, grupo_id, data_de, data_de, data_ate, data_ate, *conta_vals, *tipo_vals, *excluir_ids])  # noqa: S608
    rows = cursor.fetchall()

    meses_dict = {}
    cat_totais = {}
    cat_slugs = {}
    for r in rows:
        mes, cat, total = r["mes"], r["categoria"], r["total"]
        if mes not in meses_dict:
            meses_dict[mes] = {}
        meses_dict[mes][cat] = float(total)
        cat_totais[cat] = cat_totais.get(cat, 0) + float(total)
        cat_slugs[cat] = r["categoria_slug"]

    categorias = sorted(cat_totais.keys(), key=lambda c: cat_totais[c], reverse=True)
    return {
        "meses": [
            {"mes": mes, "categorias": {cat: meses_dict[mes].get(cat, 0.0) for cat in categorias}}
            for mes in sorted(meses_dict.keys())
        ],
        "categorias": categorias,
        "categorias_slugs": [cat_slugs[c] for c in categorias],
    }


def stats_saldo_diario(
    cursor: RealDictCursor, uid: str, conta_id: str | None, tipo: str | None,
    data_de: str | None, data_ate: str | None,
) -> list[dict]:
    """Saldo total (das contas filtradas) dia a dia, desde a âncora mais antiga até hoje."""
    conta_cond, conta_vals = lista_sql("id", conta_id)
    tipo_cond, tipo_vals = lista_sql("tipo", tipo)

    cursor.execute("""
        WITH """ + PONTOS_SALDO_CTE + """,
        contas_filtradas AS (
            SELECT id, data_ancora FROM contas
            WHERE utilizador_id = %s
    """ + conta_cond + tipo_cond + """
        ),
        dias AS (
            SELECT generate_series(
                (SELECT MIN(data_ancora) FROM contas_filtradas),
                CURRENT_DATE, '1 day'::interval
            )::date AS dia
        ),
        saldo_por_conta_dia AS (
            SELECT d.dia, cf.id AS conta_id,
                   a.saldo_real + COALESCE((
                       SELECT SUM(m.valor) FROM movimentos m
                       WHERE m.conta_id = cf.id AND m.data > a.data AND m.data <= d.dia
                   ), 0) AS saldo
            FROM dias d
            CROSS JOIN contas_filtradas cf
            CROSS JOIN LATERAL (
                SELECT saldo_real, data FROM pontos_saldo
                WHERE conta_id = cf.id AND data <= d.dia
                ORDER BY data DESC LIMIT 1
            ) a
        )
        SELECT dia, SUM(saldo) AS saldo
        FROM saldo_por_conta_dia
        GROUP BY dia
        ORDER BY dia
    """, [uid, *conta_vals, *tipo_vals])  # noqa: S608
    rows = cursor.fetchall()

    if not rows:
        return []

    pontos = [{"data": str(r["dia"]), "saldo": round(float(r["saldo"]), 2)} for r in rows]
    if data_de:
        pontos = [p for p in pontos if p["data"] >= data_de]
    if data_ate:
        pontos = [p for p in pontos if p["data"] <= data_ate]
    return pontos


def _calcular_padrao_recorrente(ocorrencias: list[tuple[date, float]]) -> dict | None:
    """Lógica pura (sem BD) do cálculo de regularidade — ocorrencias é a lista de
    (data, valor) da mesma descrição+categoria, já ordenada por data. Devolve None se não
    houver ocorrências suficientes para dizer nada (menos de 2, ou todas na mesma data)."""
    if len(ocorrencias) < 2:
        return None

    datas    = [o[0] for o in ocorrencias]
    valores  = [o[1] for o in ocorrencias]
    intervalos = [(datas[i] - datas[i - 1]).days for i in range(1, len(datas))]

    intervalo_medio = sum(intervalos) / len(intervalos)
    if intervalo_medio == 0:
        return None

    desvio  = (sum((i - intervalo_medio) ** 2 for i in intervalos) / len(intervalos)) ** 0.5
    regular = (desvio / intervalo_medio) < 0.4
    proxima_data = datas[-1] + timedelta(days=round(intervalo_medio))

    return {
        "ocorrencias": len(ocorrencias),
        "valor_medio": round(sum(valores) / len(valores), 2),
        "ultima_vez": str(datas[-1]),
        "intervalo_medio_dias": round(intervalo_medio),
        "proxima_data_estimada": str(proxima_data),
        "regular": regular,
    }


def stats_recorrentes(
    cursor: RealDictCursor, uid: str, conta_id: str | None, tipo: str | None,
    data_de: str | None, data_ate: str | None, excluir_categorias: str | None,
) -> list[dict]:
    """Deteta despesas que se repetem (mesma descrição+categoria, ≥2 ocorrências) e estima
    a próxima data — "regular" quando o desvio-padrão dos intervalos é < 40% da média."""
    conta_cond, conta_vals = lista_sql("m.conta_id", conta_id)
    tipo_cond, tipo_vals = lista_sql("ct.tipo", tipo)
    excluir_cond, excluir_ids = _excluir_sql(excluir_categorias)

    cursor.execute("""
        SELECT m.descricao, m.categoria_id, c.nome AS categoria, c.slug AS categoria_slug,
               g.nome AS grupo, g.slug AS grupo_slug, m.data, m.valor
        FROM movimentos m
        JOIN categorias c ON m.categoria_id = c.id
        JOIN categorias g ON c.parent_id = g.id
        JOIN contas ct ON m.conta_id = ct.id
        WHERE m.utilizador_id = %s AND m.valor < 0
          AND (%s IS NULL OR m.data >= %s)
          AND (%s IS NULL OR m.data <= %s)
    """ + conta_cond + tipo_cond + excluir_cond + """
        ORDER BY m.descricao, c.nome, m.data
    """, [uid, data_de, data_de, data_ate, data_ate, *conta_vals, *tipo_vals, *excluir_ids])  # noqa: S608
    rows = cursor.fetchall()

    ocorrencias_por_chave = defaultdict(list)
    info_por_chave = {}
    for r in rows:
        chave = (r["descricao"], r["categoria_id"])
        info_por_chave[chave] = (r["categoria"], r["categoria_slug"], r["grupo"], r["grupo_slug"])
        ocorrencias_por_chave[chave].append((r["data"], float(r["valor"])))

    resultado = []
    for chave, ocorrencias in ocorrencias_por_chave.items():
        padrao = _calcular_padrao_recorrente(ocorrencias)
        if padrao is None:
            continue

        descricao, _categoria_id = chave
        categoria, categoria_slug, grupo, grupo_slug = info_por_chave[chave]
        resultado.append({
            "descricao": descricao, "categoria": categoria, "categoria_slug": categoria_slug,
            "grupo": grupo, "grupo_slug": grupo_slug, **padrao
        })

    resultado.sort(key=lambda x: (not x["regular"], -x["ocorrencias"]))
    return resultado
