# ═══════════════════════════════════════════════════════════════
# IMPORTS E CONFIGURAÇÃO
# ═══════════════════════════════════════════════════════════════
from fastapi import FastAPI, HTTPException, Depends, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from collections import defaultdict
from datetime import timedelta
from email_utils import enviar_email
import uuid
from datetime import date, timedelta
import psycopg2

from database import get_connection
from auth import encriptar_password, verificar_password, criar_token, verificar_token
from nordigen import guardar_em_cache

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.mount("/static", StaticFiles(directory="static"), name="static")

security = HTTPBearer()


# ═══════════════════════════════════════════════════════════════
# MODELOS
# ═══════════════════════════════════════════════════════════════
class RegistoInput(BaseModel):
    nome:     str
    email:    str
    password: str

class LoginInput(BaseModel):
    email:    str
    password: str

class ContaInput(BaseModel):
    nome:  str
    banco: str
    tipo:  str
    iban:  str
    moeda: str
    saldo: float

class ContaEditInput(BaseModel):
    nome:  str
    banco: str
    tipo:  str
    iban:  str
    moeda: str

class AjusteSaldoCriarInput(BaseModel):
    data: str
    saldo_real: float

class AjusteSaldoEditarInput(BaseModel):
    data: str
    saldo_real: float

class MovimentoInput(BaseModel):
    conta_id:     str
    data:         str
    descricao:    str
    valor:        float
    categoria_id: int

class CategoriaInput(BaseModel):
    categoria_id: int

class CategoriaGestaoInput(BaseModel):
    nome:           str
    parent_id:      int  | None = None
    eh_recebimento: bool | None = None

class PerfilUpdateInput(BaseModel):
    nome:  str
    email: str

class PasswordUpdateInput(BaseModel):
    password_atual: str
    password_nova:  str

class EsqueciPasswordInput(BaseModel):
    email: str

class RedefinirPasswordInput(BaseModel):
    token:         str
    password_nova: str

# ═══════════════════════════════════════════════════════════════
# AUTENTICAÇÃO
# ═══════════════════════════════════════════════════════════════
def utilizador_atual(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verificar_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    return payload


@app.get("/")
def raiz():
    return {"status": "ok", "projeto": "tesouraria"}


ARVORE_PADRAO = [
    ("Trabalho", True, ["Salário", "Prémios", "Recibos Verdes", "Outros"]),
    ("Investimentos", True, ["Renda de Imóveis", "Dividendos", "Juros", "Outros"]),
    ("Venda de Ativos", True, ["Imóveis", "Veículos", "Equipamentos", "Ativos Financeiros", "Outros"]),
    ("Empréstimos", True, ["Crédito Pessoal", "Empréstimo Particular", "Outros"]),
    ("Transferências Próprias", True, ["Entre Contas", "Depósito em Numerário", "Outros"]),
    ("Outros Recebimentos", True, ["Reembolsos", "Presentes", "Donativos", "Heranças", "Outros"]),

    ("Habitação", False, ["Prestação", "Renda", "Água, Eletricidade e Gás", "Telecomunicações", "Bens Mobiliários", "Segurança", "Condomínio", "Serviços Domésticos", "Outros"]),
    ("Alimentação", False, ["Supermercado", "Restaurantes e Cafés", "Outros"]),
    ("Transportes", False, ["Prestação", "Combustível", "Manutenção e Inspeção", "Portagens e Estacionamento", "Transportes Públicos e TVDE", "Outros"]),
    ("Educação", False, ["Cursos e Formações", "Livros e Material", "Outros"]),
    ("Saúde e Auto-Cuidado", False, ["Consultas e Exames", "Tratamentos e Medicamentos", "Serviços de Bem-Estar", "Outros"]),
    ("Entretenimento", False, ["Viagens", "Eventos", "Subscrições", "Outros"]),
    ("Tecnologia", False, ["Hardware", "Software", "Outros"]),
    ("Impostos", False, ["IRS", "IUC", "IMI", "Coimas", "Outros"]),
    ("Seguros", False, ["Habitação", "Automóvel", "Saúde", "Vida", "Outros"]),
    ("Serviços Financeiros", False, ["Juros", "Comissões", "Outros"]),
    ("Compra de Ativos (para Investimento)", False, ["Imóveis", "Veículos", "Equipamentos", "Ativos Financeiros", "Outros"]),
    ("Transferências Próprias", False, ["Entre Contas", "Levantamento em Numerário", "Outros"]),
    ("Outros Pagamentos", False, ["Presentes", "Donativos", "Quotas", "Outros"]),
]


def seed_categorias_padrao(conn, utilizador_id):
    cursor = conn.cursor()
    for ordem_grupo, (nome_grupo, eh_recebimento, categorias) in enumerate(ARVORE_PADRAO, start=1):
        cursor.execute("""
            INSERT INTO categorias (nome, eh_recebimento, ordem, utilizador_id)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (nome_grupo, eh_recebimento, ordem_grupo, utilizador_id))
        grupo_id = cursor.fetchone()[0]

        for ordem_cat, nome_cat in enumerate(categorias, start=1):
            cursor.execute("""
                INSERT INTO categorias (nome, parent_id, eh_recebimento, ordem, utilizador_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (nome_cat, grupo_id, eh_recebimento, ordem_cat, utilizador_id))

    conn.commit()
    cursor.close()


@app.post("/registro")
@limiter.limit("5/minute")
def registar(request: Request, dados: RegistoInput):
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

    seed_categorias_padrao(conn, utilizador_id)
    conn.close()

    token = criar_token({"sub": str(utilizador_id), "email": dados.email})
    return {"token": token, "nome": dados.nome}


@app.post("/login")
@limiter.limit("5/minute")
def login(request: Request, dados: LoginInput):
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


@app.put("/me")
def atualizar_perfil(dados: PerfilUpdateInput, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE utilizadores SET nome=%s, email=%s WHERE id=%s", (dados.nome, dados.email, utilizador["sub"]))
    conn.commit()
    cursor.close(); conn.close()
    return {"ok": True, "nome": dados.nome}


@app.put("/me/password")
def atualizar_password(dados: PasswordUpdateInput, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM utilizadores WHERE id=%s", (utilizador["sub"],))
    hash_atual = cursor.fetchone()[0]
    if not verificar_password(dados.password_atual, hash_atual):
        cursor.close(); conn.close()
        raise HTTPException(status_code=401, detail="Password atual incorreta")
    cursor.execute("UPDATE utilizadores SET password=%s WHERE id=%s", (encriptar_password(dados.password_nova), utilizador["sub"]))
    conn.commit()
    cursor.close(); conn.close()
    return {"ok": True}

@app.post("/esqueci-password")
@limiter.limit("3/hour")
def esqueci_password(request: Request, dados: EsqueciPasswordInput):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM utilizadores WHERE email = %s", (dados.email,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row:
        token = criar_token({"sub": str(row[0]), "tipo": "reset"}, timedelta(hours=1))
        link = f"http://localhost:8000/static/index.html?token={token}"
        enviar_email(
            dados.email,
            "Recuperar password — Tesouraria",
            f"Clica neste link para definires uma password nova (válido por 1 hora):\n\n{link}"
        )

    return {"ok": True, "mensagem": "Se o email existir, enviámos instruções."}


@app.post("/redefinir-password")
def redefinir_password(dados: RedefinirPasswordInput):
    payload = verificar_token(dados.token)
    if not payload or payload.get("tipo") != "reset":
        raise HTTPException(status_code=400, detail="Link inválido ou expirado")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE utilizadores SET password = %s WHERE id = %s",
        (encriptar_password(dados.password_nova), payload["sub"])
    )
    conn.commit()
    cursor.close()
    conn.close()
    return {"ok": True}

@app.delete("/me")
def eliminar_conta_utilizador(utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]
    cursor.execute("DELETE FROM categorias_aprendidas WHERE utilizador_id=%s", (uid,))
    cursor.execute("DELETE FROM movimentos WHERE utilizador_id=%s", (uid,))
    cursor.execute("DELETE FROM categorias WHERE utilizador_id=%s", (uid,))
    cursor.execute("DELETE FROM ajustes_saldo WHERE conta_id IN (SELECT id FROM contas WHERE utilizador_id=%s)", (uid,))
    cursor.execute("DELETE FROM contas WHERE utilizador_id=%s", (uid,))
    cursor.execute("DELETE FROM utilizadores WHERE id=%s", (uid,))
    conn.commit()
    cursor.close(); conn.close()
    return {"ok": True}

# ═══════════════════════════════════════════════════════════════
# CONTAS
# ═══════════════════════════════════════════════════════════════
@app.get("/contas")
def listar_contas(utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nome, banco, iban, moeda, saldo, tipo
        FROM contas
        WHERE utilizador_id = %s
        ORDER BY nome
    """, (utilizador["sub"],))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [
        {"id": r[0], "nome": r[1], "banco": r[2], "iban": r[3], "moeda": r[4], "saldo": float(r[5]), "tipo": r[6]}
        for r in rows
    ]


@app.post("/contas")
def criar_conta(dados: ContaInput, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    conta_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO contas (id, nome, banco, iban, moeda, saldo, tipo, utilizador_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (conta_id, dados.nome, dados.banco, dados.iban, dados.moeda, dados.saldo, dados.tipo, utilizador["sub"]))
    cursor.execute("""
        INSERT INTO ajustes_saldo (conta_id, data, saldo_real) VALUES (%s, CURRENT_DATE, %s)
    """, (conta_id, dados.saldo))
    conn.commit()
    cursor.close()
    conn.close()
    return {"ok": True}


@app.put("/contas/{conta_id}")
def editar_conta(conta_id: str, dados: ContaEditInput, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE contas SET nome=%s, banco=%s, iban=%s, moeda=%s, tipo=%s
        WHERE id=%s AND utilizador_id=%s
    """, (dados.nome, dados.banco, dados.iban, dados.moeda, dados.tipo, conta_id, utilizador["sub"]))
    conn.commit()
    cursor.close()
    conn.close()
    return {"ok": True}


def atualizar_saldo_atual(cursor, conta_id):
    cursor.execute("""
        SELECT saldo_real FROM ajustes_saldo WHERE conta_id=%s ORDER BY data DESC LIMIT 1
    """, (conta_id,))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE contas SET saldo=%s WHERE id=%s", (row[0], conta_id))


@app.get("/contas/{conta_id}/ajustes-saldo")
def listar_ajustes_saldo(conta_id: str, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.data, a.saldo_real FROM ajustes_saldo a
        JOIN contas c ON a.conta_id = c.id
        WHERE a.conta_id=%s AND c.utilizador_id=%s
        ORDER BY a.data DESC
    """, (conta_id, utilizador["sub"]))
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return [{"id": r[0], "data": str(r[1]), "saldo_real": float(r[2])} for r in rows]


@app.post("/contas/{conta_id}/ajustes-saldo")
def criar_ajuste_saldo(conta_id: str, dados: AjusteSaldoCriarInput, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]

    cursor.execute("SELECT id FROM contas WHERE id=%s AND utilizador_id=%s", (conta_id, uid))
    if not cursor.fetchone():
        cursor.close(); conn.close()
        raise HTTPException(status_code=404, detail="Conta não encontrada")

    if dados.data > str(date.today()):
        cursor.close(); conn.close()
        raise HTTPException(status_code=400, detail="Não é possível reconciliar uma data futura.")

    try:
        cursor.execute("""
            INSERT INTO ajustes_saldo (conta_id, data, saldo_real) VALUES (%s, %s, %s)
        """, (conta_id, dados.data, dados.saldo_real))
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        cursor.close(); conn.close()
        raise HTTPException(status_code=400, detail="Já existe uma reconciliação nessa data.")

    atualizar_saldo_atual(cursor, conta_id)
    conn.commit()
    cursor.close(); conn.close()
    return {"ok": True}


@app.put("/ajustes-saldo/{ajuste_id}")
def editar_ajuste_saldo(ajuste_id: int, dados: AjusteSaldoEditarInput, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]

    cursor.execute("""
        SELECT a.conta_id FROM ajustes_saldo a
        JOIN contas c ON a.conta_id = c.id
        WHERE a.id=%s AND c.utilizador_id=%s
    """, (ajuste_id, uid))
    row = cursor.fetchone()
    if not row:
        cursor.close(); conn.close()
        raise HTTPException(status_code=404, detail="Reconciliação não encontrada")
    conta_id = row[0]

    if dados.data > str(date.today()):
        cursor.close(); conn.close()
        raise HTTPException(status_code=400, detail="Não é possível reconciliar uma data futura.")

    try:
        cursor.execute("UPDATE ajustes_saldo SET data=%s, saldo_real=%s WHERE id=%s", (dados.data, dados.saldo_real, ajuste_id))
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        cursor.close(); conn.close()
        raise HTTPException(status_code=400, detail="Já existe uma reconciliação nessa data.")

    atualizar_saldo_atual(cursor, conta_id)
    conn.commit()
    cursor.close(); conn.close()
    return {"ok": True}


@app.delete("/ajustes-saldo/{ajuste_id}")
def eliminar_ajuste_saldo(ajuste_id: int, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]

    cursor.execute("""
        SELECT a.conta_id FROM ajustes_saldo a
        JOIN contas c ON a.conta_id = c.id
        WHERE a.id=%s AND c.utilizador_id=%s
    """, (ajuste_id, uid))
    row = cursor.fetchone()
    if not row:
        cursor.close(); conn.close()
        raise HTTPException(status_code=404, detail="Reconciliação não encontrada")
    conta_id = row[0]

    cursor.execute("SELECT COUNT(*) FROM ajustes_saldo WHERE conta_id=%s", (conta_id,))
    if cursor.fetchone()[0] <= 1:
        cursor.close(); conn.close()
        raise HTTPException(status_code=400, detail="Uma conta precisa de pelo menos uma reconciliação.")

    cursor.execute("DELETE FROM ajustes_saldo WHERE id=%s", (ajuste_id,))
    atualizar_saldo_atual(cursor, conta_id)
    conn.commit()
    cursor.close(); conn.close()
    return {"ok": True}


@app.delete("/contas/{conta_id}")
def eliminar_conta(conta_id: str, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM movimentos WHERE conta_id = %s AND utilizador_id = %s
    """, (conta_id, utilizador["sub"]))
    n = cursor.fetchone()[0]
    if n > 0:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail=f"Esta conta tem {n} movimento(s) associados. Elimina-os primeiro.")

    cursor.execute("DELETE FROM contas WHERE id = %s AND utilizador_id = %s", (conta_id, utilizador["sub"]))
    conn.commit()
    cursor.close()
    conn.close()
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════
# CATEGORIAS
# ═══════════════════════════════════════════════════════════════
@app.get("/categorias")
def listar_categorias(utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT c.id, c.nome, g.nome AS grupo, g.eh_recebimento
        FROM categorias c
        JOIN categorias g ON c.parent_id = g.id
        WHERE c.utilizador_id = %s
          AND NOT EXISTS (SELECT 1 FROM categorias f WHERE f.parent_id = c.id)
        ORDER BY g.eh_recebimento DESC, g.ordem, c.ordem
    """, (utilizador["sub"],))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [{"id": r[0], "nome": r[1], "grupo": r[2], "eh_recebimento": r[3]} for r in rows]

@app.get("/categorias/arvore")
def arvore_categorias(utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]

    cursor.execute("""
        SELECT id, nome, eh_recebimento FROM categorias
        WHERE utilizador_id=%s AND parent_id IS NULL
        ORDER BY ordem
    """, (uid,))
    grupos = cursor.fetchall()

    cursor.execute("""
        SELECT id, nome, parent_id FROM categorias
        WHERE utilizador_id=%s AND parent_id IS NOT NULL
        ORDER BY ordem
    """, (uid,))
    categorias = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        {
            "id": gid, "nome": nome, "eh_recebimento": eh_rec,
            "categorias": [{"id": c[0], "nome": c[1]} for c in categorias if c[2] == gid]
        }
        for gid, nome, eh_rec in grupos
    ]


@app.post("/categorias")
def criar_categoria(dados: CategoriaGestaoInput, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]

    if dados.parent_id is None and dados.eh_recebimento is None:
        cursor.close(); conn.close()
        raise HTTPException(status_code=400, detail="Um grupo novo precisa de indicar se é Entrada ou Saída.")

    if dados.parent_id is None:
        cursor.execute("SELECT COALESCE(MAX(ordem),0)+1 FROM categorias WHERE utilizador_id=%s AND parent_id IS NULL", (uid,))
        eh_recebimento = dados.eh_recebimento
    else:
        cursor.execute("SELECT COALESCE(MAX(ordem),0)+1 FROM categorias WHERE parent_id=%s", (dados.parent_id,))
        cursor.execute("SELECT eh_recebimento FROM categorias WHERE id=%s", (dados.parent_id,))
        eh_recebimento = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(MAX(ordem),0)+1 FROM categorias WHERE parent_id=%s", (dados.parent_id,))
    ordem = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO categorias (nome, parent_id, eh_recebimento, ordem, utilizador_id)
        VALUES (%s, %s, %s, %s, %s)
    """, (dados.nome, dados.parent_id, eh_recebimento, ordem, uid))
    conn.commit()
    cursor.close(); conn.close()
    return {"ok": True}


@app.put("/categorias/{categoria_id}")
def editar_categoria_nome(categoria_id: int, dados: CategoriaGestaoInput, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]

    cursor.execute("SELECT parent_id FROM categorias WHERE id=%s AND utilizador_id=%s", (categoria_id, uid))
    row = cursor.fetchone()
    if not row:
        cursor.close(); conn.close()
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    eh_grupo = row[0] is None

    if dados.parent_id is not None:
        if eh_grupo:
            cursor.close(); conn.close()
            raise HTTPException(status_code=400, detail="Um grupo não pode ser movido para dentro de outro grupo.")
        cursor.execute("SELECT eh_recebimento FROM categorias WHERE id=%s", (dados.parent_id,))
        eh_recebimento = cursor.fetchone()[0]
        cursor.execute("""
            UPDATE categorias SET nome=%s, parent_id=%s, eh_recebimento=%s
            WHERE id=%s AND utilizador_id=%s
        """, (dados.nome, dados.parent_id, eh_recebimento, categoria_id, uid))
    else:
        cursor.execute("""
            UPDATE categorias SET nome=%s WHERE id=%s AND utilizador_id=%s
        """, (dados.nome, categoria_id, uid))

    conn.commit()
    cursor.close(); conn.close()
    return {"ok": True}


@app.delete("/categorias/{categoria_id}")
def eliminar_categoria(categoria_id: int, migrar_para_id: int = None, forcar: bool = False, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]

    cursor.execute("SELECT parent_id FROM categorias WHERE id=%s AND utilizador_id=%s", (categoria_id, uid))
    row = cursor.fetchone()
    if not row:
        cursor.close(); conn.close()
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    parent_id = row[0]

    if parent_id is None:
        cursor.execute("SELECT COUNT(*) FROM categorias WHERE parent_id=%s", (categoria_id,))
        n = cursor.fetchone()[0]
        if n > 0 and not migrar_para_id and not forcar:
            cursor.close(); conn.close()
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
    else:
        cursor.execute("SELECT COUNT(*) FROM movimentos WHERE categoria_id=%s", (categoria_id,))
        n = cursor.fetchone()[0]
        if n > 0 and not migrar_para_id and not forcar:
            cursor.close(); conn.close()
            raise HTTPException(status_code=400, detail=f"{n} transação(ões) usam esta categoria.")
        if n > 0 and migrar_para_id:
            cursor.execute("UPDATE movimentos SET categoria_id=%s WHERE categoria_id=%s", (migrar_para_id, categoria_id))
            cursor.execute("DELETE FROM categorias_aprendidas WHERE categoria_id=%s", (categoria_id,))
        elif n > 0 and forcar:
            cursor.execute("DELETE FROM movimentos WHERE categoria_id=%s", (categoria_id,))
            cursor.execute("DELETE FROM categorias_aprendidas WHERE categoria_id=%s", (categoria_id,))
        cursor.execute("DELETE FROM categorias WHERE id=%s", (categoria_id,))

    conn.commit()
    cursor.close(); conn.close()
    return {"ok": True}


@app.post("/categorias/{categoria_id}/mover")
def mover_categoria(categoria_id: int, direcao: str, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]

    cursor.execute("SELECT parent_id, ordem, eh_recebimento FROM categorias WHERE id=%s AND utilizador_id=%s", (categoria_id, uid))
    row = cursor.fetchone()
    if not row:
        cursor.close(); conn.close()
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

    cursor.close(); conn.close()
    return {"ok": True}

# ═══════════════════════════════════════════════════════════════
# MOVIMENTOS
# ═══════════════════════════════════════════════════════════════
@app.get("/movimentos")
def listar_movimentos(
    utilizador: dict = Depends(utilizador_atual),
    conta_id: str = None,
    categoria_id: int = None,
    direcao: str = None,
    data_de: str = None,
    data_ate: str = None,
):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]

    filtro_direcao = ""
    if direcao == "in":
        filtro_direcao = "AND m.valor > 0"
    elif direcao == "out":
        filtro_direcao = "AND m.valor < 0"

    cursor.execute("""
        SELECT m.id, m.conta_id, m.data, m.descricao, m.valor,
               m.categoria_id, c.nome, g.nome, m.origem_cat
        FROM movimentos m
        JOIN categorias c ON m.categoria_id = c.id
        JOIN categorias g ON c.parent_id = g.id
        WHERE m.utilizador_id = %s
          AND (%s IS NULL OR m.conta_id = %s)
          AND (%s IS NULL OR m.categoria_id = %s)
          AND (%s IS NULL OR m.data >= %s)
          AND (%s IS NULL OR m.data <= %s)
    """ + filtro_direcao + """
        ORDER BY m.data DESC
    """, [uid, conta_id, conta_id, categoria_id, categoria_id, data_de, data_de, data_ate, data_ate])
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return [
        {
            "id": r[0], "conta_id": r[1], "data": str(r[2]), "descricao": r[3], "valor": float(r[4]),
            "categoria_id": r[5], "categoria": r[6], "grupo": r[7], "origem_cat": r[8],
        }
        for r in rows
    ]


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


@app.put("/movimentos/{movimento_id}")
def editar_movimento(movimento_id: str, dados: MovimentoInput, utilizador: dict = Depends(utilizador_atual)):
    conn   = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]

    cursor.execute("""
        UPDATE movimentos
        SET conta_id=%s, data=%s, descricao=%s, valor=%s, categoria_id=%s, origem_cat='manual'
        WHERE id=%s AND utilizador_id=%s
    """, (dados.conta_id, dados.data, dados.descricao, dados.valor, dados.categoria_id, movimento_id, uid))
    conn.commit()

    guardar_em_cache(conn, dados.descricao, dados.categoria_id, uid)

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


# ═══════════════════════════════════════════════════════════════
# ESTATÍSTICAS
# ═══════════════════════════════════════════════════════════════
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
def stats_mensal(utilizador: dict = Depends(utilizador_atual), conta_id: str = None, tipo: str = None, data_de: str = None, data_ate: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]

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
    cursor.close()
    conn.close()

    return [
        {"mes": r[0], "entradas": float(r[1]), "saidas": float(r[2]), "liquido": float(r[1]) - float(r[2])}
        for r in rows
    ]


@app.get("/stats/categorias")
def stats_categorias(utilizador: dict = Depends(utilizador_atual), conta_id: str = None, tipo: str = None, data_de: str = None, data_ate: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]

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
    cursor.close()
    conn.close()

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


@app.get("/stats/grupos")
def stats_grupos(utilizador: dict = Depends(utilizador_atual), conta_id: str = None, tipo: str = None, data_de: str = None, data_ate: str = None):
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
    cursor.close()
    conn.close()

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


@app.get("/stats/saldo-mensal")
def stats_saldo_mensal(utilizador: dict = Depends(utilizador_atual), conta_id: str = None, tipo: str = None, data_de: str = None, data_ate: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]

    cursor.execute("""
        SELECT SUM(saldo) FROM contas
        WHERE utilizador_id = %s
          AND (%s IS NULL OR id = %s)
          AND (%s IS NULL OR tipo = %s)
    """, [uid, conta_id, conta_id, tipo, tipo])
    saldo_atual = float(cursor.fetchone()[0] or 0)

    cursor.execute("""
        SELECT TO_CHAR(DATE_TRUNC('month', m.data), 'YYYY-MM') AS mes, SUM(m.valor) AS soma_mes
        FROM movimentos m
        JOIN contas ct ON m.conta_id = ct.id
        WHERE m.utilizador_id = %s
          AND (%s IS NULL OR m.conta_id = %s)
          AND (%s IS NULL OR ct.tipo = %s)
        GROUP BY DATE_TRUNC('month', m.data)
        ORDER BY DATE_TRUNC('month', m.data)
    """, [uid, conta_id, conta_id, tipo, tipo])
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    acumulado = 0.0
    pontos = []
    for mes, soma in rows:
        acumulado += float(soma)
        pontos.append({"mes": mes, "acumulado": acumulado})

    offset = saldo_atual - (pontos[-1]["acumulado"] if pontos else 0)
    pontos = [{"mes": p["mes"], "saldo": round(p["acumulado"] + offset, 2)} for p in pontos]

    if data_de:
        pontos = [p for p in pontos if p["mes"] >= data_de[:7]]
    if data_ate:
        pontos = [p for p in pontos if p["mes"] <= data_ate[:7]]

    return pontos


@app.get("/stats/saldo-diario")
def stats_saldo_diario(utilizador: dict = Depends(utilizador_atual), conta_id: str = None, tipo: str = None, data_de: str = None, data_ate: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]

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
                       WHERE m.conta_id = cf.id AND m.data > a.data AND m.data <= d.dia
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
    cursor.close()
    conn.close()

    if not rows:
        return []

    pontos = [{"data": str(r[0]), "saldo": round(float(r[1]), 2)} for r in rows]

    if data_de:
        pontos = [p for p in pontos if p["data"] >= data_de]
    if data_ate:
        pontos = [p for p in pontos if p["data"] <= data_ate]

    return pontos

# arrancar servidor
# uvicorn main:app --reload
# http://localhost:8000/static/index.html