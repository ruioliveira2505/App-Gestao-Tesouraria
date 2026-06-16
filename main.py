from fastapi import FastAPI
from database import get_connection
from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from auth import encriptar_password, verificar_password, criar_token, verificar_token

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

class RegistoInput(BaseModel):
    nome:     str
    email:    str
    password: str

class LoginInput(BaseModel):
    email:    str
    password: str

def utilizador_atual(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verificar_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    return payload

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

@app.get("/")
def raiz():
    return {"status": "ok", "projeto": "tesouraria"}

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

@app.get("/movimentos")
def listar_movimentos(utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, conta_id, data, descricao, valor, categoria, origem_cat
        FROM movimentos
        WHERE utilizador_id = %s
        ORDER BY data DESC
    """, (utilizador["sub"],))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        {
            "id":         r[0],
            "conta_id":   r[1],
            "data":       str(r[2]),
            "descricao":  r[3],
            "valor":      float(r[4]),
            "categoria":  r[5],
            "origem_cat": r[6],
        }
        for r in rows
    ]

@app.get("/resumo")
def resumo(utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            categoria,
            COUNT(*)                                AS n,
            SUM(CASE WHEN valor > 0 THEN valor END) AS entradas,
            SUM(CASE WHEN valor < 0 THEN valor END) AS saidas
        FROM movimentos
        WHERE utilizador_id = %s
        GROUP BY categoria
        ORDER BY categoria
    """, (utilizador["sub"],))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        {
            "categoria": r[0],
            "n":         r[1],
            "entradas":  float(r[2] or 0),
            "saidas":    float(r[3] or 0),
        }
        for r in rows
    ]

@app.get("/me")
def perfil(utilizador: dict = Depends(utilizador_atual)):
    return {"email": utilizador["email"], "id": utilizador["sub"]}

@app.get("/stats/mensal")
def stats_mensal(utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            DATE_TRUNC('month', data)               AS mes,
            SUM(CASE WHEN valor > 0 THEN valor END) AS entradas,
            SUM(CASE WHEN valor < 0 THEN valor END) AS saidas
        FROM movimentos
        WHERE utilizador_id = %s
        GROUP BY mes
        ORDER BY mes
    """, (utilizador["sub"],))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        {
            "mes":      str(r[0])[:7],
            "entradas": float(r[1] or 0),
            "saidas":   float(r[2] or 0),
            "liquido":  float((r[1] or 0) + (r[2] or 0)),
        }
        for r in rows
    ]

@app.get("/stats/categorias")
def stats_categorias(utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            categoria,
            COUNT(*)                                        AS n,
            SUM(CASE WHEN valor < 0 THEN ABS(valor) END)   AS total_gasto
        FROM movimentos
        WHERE utilizador_id = %s
        AND valor < 0
        AND categoria != 'por categorizar'
        GROUP BY categoria
        ORDER BY total_gasto DESC
    """, (utilizador["sub"],))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    total = sum(float(r[2] or 0) for r in rows)

    return [
        {
            "categoria":   r[0],
            "n":           r[1],
            "total":       float(r[2] or 0),
            "percentagem": round(float(r[2] or 0) / total * 100, 1) if total else 0,
        }
        for r in rows
    ]

@app.get("/stats/recorrentes")
def stats_recorrentes(utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            descricao,
            categoria,
            COUNT(*)        AS ocorrencias,
            AVG(valor)      AS valor_medio,
            MAX(data)       AS ultima_vez
        FROM movimentos
        WHERE utilizador_id = %s
        GROUP BY descricao, categoria
        HAVING COUNT(*) > 1
        ORDER BY ocorrencias DESC, ABS(AVG(valor)) DESC
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
        {
            "data":  str(r[0]),
            "saldo": round(float(r[1]), 2),
        }
        for r in rows
    ]


class MovimentoInput(BaseModel):
    conta_id:  str
    data:      str
    descricao: str
    valor:     float
    categoria: str

class CategoriaInput(BaseModel):
    categoria: str

@app.post("/movimentos")
def criar_movimento(dados: MovimentoInput, utilizador: dict = Depends(utilizador_atual)):
    import uuid
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO movimentos (id, conta_id, data, descricao, valor, categoria, origem_cat, utilizador_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (str(uuid.uuid4()), dados.conta_id, dados.data, dados.descricao, dados.valor, dados.categoria, "manual", utilizador["sub"]))
    conn.commit()
    cursor.close()
    conn.close()
    return {"ok": True}

@app.patch("/movimentos/{movimento_id}/categoria")
def editar_categoria(movimento_id: str, dados: CategoriaInput, utilizador: dict = Depends(utilizador_atual)):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE movimentos SET categoria = %s, origem_cat = 'manual'
        WHERE id = %s AND utilizador_id = %s
    """, (dados.categoria, movimento_id, utilizador["sub"]))
    conn.commit()
    cursor.close()
    conn.close()
    return {"ok": True}

# arrancar servidor
# uvicorn main:app --reload