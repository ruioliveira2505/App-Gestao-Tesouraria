from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import uuid

from database import get_connection
from auth import encriptar_password, verificar_password, criar_token, verificar_token
from nordigen import guardar_em_cache

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

security = HTTPBearer()


class RegistoInput(BaseModel):
    nome:     str
    email:    str
    password: str

class LoginInput(BaseModel):
    email:    str
    password: str

class MovimentoInput(BaseModel):
    conta_id:     str
    data:         str
    descricao:    str
    valor:        float
    categoria_id: int

class CategoriaInput(BaseModel):
    categoria_id: int


def utilizador_atual(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verificar_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    return payload


@app.get("/")
def raiz():
    return {"status": "ok", "projeto": "tesouraria"}


@app.post("/registro")
def registar(dados: RegistoInput):
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM utilizadores WHERE email = %s", (dados.email,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Email já registado")

    hash_pw = encriptar_password(dados.password)
    cursor.execute(
        "INSERT INTO utilizadores (nome, email, password) VALUES (%s, %s, %s) RETURNING id",
        (dados.nome, dados.email, hash_pw)
    )
    utilizador_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()

    token = criar_token({"sub": str(utilizador_id), "email": dados.email})
    return {"token": token, "nome": dados.nome}


@app.post("/login")
def login(dados: LoginInput):
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, nome, password FROM utilizadores WHERE email = %s",
        (dados.email,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row or not verificar_password(dados.password, row[2]):
        raise HTTPException(status_code=401, detail="Email ou password incorretos")

    token = criar_token({"sub": str(row[0]), "email": dados.email})
    return {"token": token, "nome": row[1]}


@app.get("/me")
def perfil(utilizador: dict = Depends(utilizador_atual)):
    return {"email": utilizador["email"], "id": utilizador["sub"]}


@app.get("/contas")
def listar_contas(utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, banco, iban, moeda, saldo
        FROM contas
        WHERE utilizador_id = %s
        ORDER BY banco
    """, (utilizador["sub"],))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        {"id": r[0], "banco": r[1], "iban": r[2], "moeda": r[3], "saldo": float(r[4])}
        for r in rows
    ]


@app.get("/categorias")
def listar_categorias(utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT c.id, c.nome, g.nome AS grupo
        FROM categorias c
        JOIN categorias g ON c.parent_id = g.id
        WHERE c.utilizador_id = %s
          AND NOT EXISTS (SELECT 1 FROM categorias f WHERE f.parent_id = c.id)
        ORDER BY g.nome, c.nome
    """, (utilizador["sub"],))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [{"id": r[0], "nome": r[1], "grupo": r[2]} for r in rows]


@app.get("/movimentos")
def listar_movimentos(utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT m.id, m.conta_id, m.data, m.descricao, m.valor,
               m.categoria_id, c.nome, g.nome, m.origem_cat
        FROM movimentos m
        JOIN categorias c ON m.categoria_id = c.id
        JOIN categorias g ON c.parent_id = g.id
        WHERE m.utilizador_id = %s
        ORDER BY m.data DESC
    """, (utilizador["sub"],))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        {
            "id":           r[0],
            "conta_id":     r[1],
            "data":         str(r[2]),
            "descricao":    r[3],
            "valor":        float(r[4]),
            "categoria_id": r[5],
            "categoria":    r[6],
            "grupo":        r[7],
            "origem_cat":   r[8],
        }
        for r in rows
    ]


@app.delete("/movimentos/{movimento_id}")
def eliminar_movimento(movimento_id: str, utilizador: dict = Depends(utilizador_atual)):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM movimentos WHERE id = %s AND utilizador_id = %s
    """, (movimento_id, utilizador["sub"]))
    conn.commit()
    cursor.close()
    conn.close()
    return {"ok": True}


@app.post("/movimentos")
def criar_movimento(dados: MovimentoInput, utilizador: dict = Depends(utilizador_atual)):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO movimentos (id, conta_id, data, descricao, valor, categoria_id, origem_cat, utilizador_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        str(uuid.uuid4()), dados.conta_id, dados.data, dados.descricao,
        dados.valor, dados.categoria_id, "manual", utilizador["sub"]
    ))
    conn.commit()
    cursor.close()
    conn.close()
    return {"ok": True}


@app.patch("/movimentos/{movimento_id}/categoria")
def editar_categoria(movimento_id: str, dados: CategoriaInput, utilizador: dict = Depends(utilizador_atual)):
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT descricao FROM movimentos WHERE id = %s AND utilizador_id = %s
    """, (movimento_id, utilizador["sub"]))
    row = cursor.fetchone()

    cursor.execute("""
        UPDATE movimentos SET categoria_id = %s, origem_cat = 'manual'
        WHERE id = %s AND utilizador_id = %s
    """, (dados.categoria_id, movimento_id, utilizador["sub"]))
    conn.commit()

    if row:
        guardar_em_cache(conn, row[0], dados.categoria_id, utilizador["sub"])

    cursor.close()
    conn.close()
    return {"ok": True}


@app.get("/resumo")
def resumo(utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            c.nome AS categoria,
            COUNT(*) AS n,
            SUM(CASE WHEN m.valor > 0 THEN m.valor END) AS entradas,
            SUM(CASE WHEN m.valor < 0 THEN m.valor END) AS saidas
        FROM movimentos m
        JOIN categorias c ON m.categoria_id = c.id
        WHERE m.utilizador_id = %s
        GROUP BY c.nome
        ORDER BY c.nome
    """, (utilizador["sub"],))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        {"categoria": r[0], "n": r[1], "entradas": float(r[2] or 0), "saidas": float(r[3] or 0)}
        for r in rows
    ]


@app.get("/stats/mensal")
def stats_mensal(utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            TO_CHAR(DATE_TRUNC('month', data), 'YYYY-MM') AS mes,
            SUM(CASE WHEN valor > 0 THEN valor ELSE 0 END) AS entradas,
            SUM(CASE WHEN valor < 0 THEN ABS(valor) ELSE 0 END) AS saidas
        FROM movimentos
        WHERE utilizador_id = %s
        GROUP BY DATE_TRUNC('month', data)
        ORDER BY DATE_TRUNC('month', data)
    """, (utilizador["sub"],))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        {
            "mes":      r[0],
            "entradas": float(r[1]),
            "saidas":   float(r[2]),
            "liquido":  float(r[1]) - float(r[2]),
        }
        for r in rows
    ]


@app.get("/stats/categorias")
def stats_categorias(utilizador: dict = Depends(utilizador_atual), mes: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]
    params = [uid, uid, mes or uid, mes or uid]

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
        JOIN arvore a ON m.categoria_id = a.id
        WHERE m.utilizador_id = %s
          AND (%s IS NULL OR TO_CHAR(m.data, 'YYYY-MM') = %s)
          AND NOT EXISTS (SELECT 1 FROM categorias f WHERE f.parent_id = a.id)
        GROUP BY a.grupo_raiz, a.caminho, a.eh_recebimento
        ORDER BY a.eh_recebimento DESC, total DESC
    """, [uid, uid, mes, mes])

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    total_out = sum(float(r[4]) for r in rows if not r[2])
    total_in  = sum(float(r[4]) for r in rows if r[2])

    return [
        {
            "grupo":          r[0],
            "categoria":      r[1],
            "eh_recebimento": r[2],
            "n":              r[3],
            "total":          float(r[4]),
            "percentagem":    round(float(r[4]) / (total_in if r[2] else total_out) * 100, 1)
                              if (total_in if r[2] else total_out) else 0,
        }
        for r in rows
    ]


@app.get("/stats/grupos")
def stats_grupos(utilizador: dict = Depends(utilizador_atual), mes: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]

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
        JOIN arvore a ON m.categoria_id = a.id
        WHERE m.utilizador_id = %s
          AND (%s IS NULL OR TO_CHAR(m.data, 'YYYY-MM') = %s)
          AND NOT EXISTS (SELECT 1 FROM categorias f WHERE f.parent_id = a.id)
        GROUP BY a.grupo_raiz, a.eh_recebimento, a.nome, a.nivel
        ORDER BY a.eh_recebimento DESC, a.grupo_raiz, total DESC
    """, [uid, uid, mes, mes])

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    from collections import defaultdict
    grupos = defaultdict(lambda: {"eh_recebimento": None, "total": 0.0, "subcategorias": []})

    for r in rows:
        grupos[r[0]]["eh_recebimento"] = r[1]
        grupos[r[0]]["total"] += float(r[5])
        grupos[r[0]]["subcategorias"].append({
            "categoria": r[2], "total": float(r[5]), "n": r[4]
        })

    return [
        {
            "grupo":          grupo,
            "eh_recebimento": dados["eh_recebimento"],
            "total":          round(dados["total"], 2),
            "subcategorias":  sorted(dados["subcategorias"], key=lambda x: x["total"], reverse=True),
        }
        for grupo, dados in sorted(
            grupos.items(),
            key=lambda x: (not x[1]["eh_recebimento"], -x[1]["total"])
        )
    ]


@app.get("/stats/recorrentes")
def stats_recorrentes(utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            m.descricao,
            c.nome AS categoria,
            COUNT(*) AS ocorrencias,
            AVG(m.valor) AS valor_medio,
            MAX(m.data) AS ultima_vez
        FROM movimentos m
        JOIN categorias c ON m.categoria_id = c.id
        WHERE m.utilizador_id = %s
        GROUP BY m.descricao, c.nome
        HAVING COUNT(*) > 1
        ORDER BY ocorrencias DESC, ABS(AVG(m.valor)) DESC
    """, (utilizador["sub"],))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        {
            "descricao":   r[0],
            "categoria":   r[1],
            "ocorrencias": r[2],
            "valor_medio": round(float(r[3]), 2),
            "ultima_vez":  str(r[4]),
        }
        for r in rows
    ]


@app.get("/stats/saldo-historico")
def stats_saldo_historico(utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            data,
            SUM(valor) OVER (ORDER BY data ROWS UNBOUNDED PRECEDING) AS saldo_acumulado
        FROM movimentos
        WHERE utilizador_id = %s
        ORDER BY data
    """, (utilizador["sub"],))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        {"data": str(r[0]), "saldo": round(float(r[1]), 2)}
        for r in rows
    ]

# arrancar servidor
# uvicorn main:app --reload