from datetime import timedelta

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from app.core.config import settings
from app.core.limiter import limiter
from app.core.security import encriptar_password, verificar_password, criar_token, verificar_token
from app.db.database import get_connection, release_connection, release_connection
from app.schemas.auth import RegistoInput, LoginInput, EsqueciPasswordInput, RedefinirPasswordInput
from app.services.categorias_seed import seed_categorias_padrao
from app.services.email import enviar_email
import uuid

router = APIRouter()


@router.post("/registro")
@limiter.limit("5/minute")
def registar(request: Request, dados: RegistoInput):
    conn = get_connection()
    cursor = conn.cursor()
    try:
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
        seed_categorias_padrao(conn, utilizador_id)
    finally:
        cursor.close()
        release_connection(conn)

    token = criar_token({"sub": str(utilizador_id), "email": dados.email})
    return {"token": token, "nome": dados.nome}


@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, dados: LoginInput):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, nome, password FROM utilizadores WHERE email = %s",
            (dados.email,)
        )
        row = cursor.fetchone()
    finally:
        cursor.close()
        release_connection(conn)

    if not row or not verificar_password(dados.password, row[2]):
        raise HTTPException(status_code=401, detail="Email ou password incorretos")

    token = criar_token({"sub": str(row[0]), "email": dados.email})
    return {"token": token, "nome": row[1]}


@router.post("/esqueci-password")
@limiter.limit("3/hour")
def esqueci_password(request: Request, dados: EsqueciPasswordInput, background_tasks: BackgroundTasks):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM utilizadores WHERE email = %s", (dados.email,))
        row = cursor.fetchone()
        jti = None
        if row:
            jti = str(uuid.uuid4())
            cursor.execute("UPDATE utilizadores SET reset_token_jti = %s WHERE id = %s", (jti, row[0]))
            conn.commit()
    finally:
        cursor.close()
        release_connection(conn)

    if row:
        token = criar_token({"sub": str(row[0]), "tipo": "reset", "jti": jti}, timedelta(hours=1))
        link = f"{settings.BASE_URL}/static/index.html?token={token}"
        background_tasks.add_task(
            enviar_email, dados.email, "Recuperar password — Tesouraria",
            f"Clica neste link para definires uma password nova (válido por 1 hora):\n\n{link}"
        )
    return {"ok": True, "mensagem": "Se o email existir, enviámos instruções."}


@router.post("/redefinir-password")
def redefinir_password(dados: RedefinirPasswordInput):
    payload = verificar_token(dados.token)
    if not payload or payload.get("tipo") != "reset":
        raise HTTPException(status_code=400, detail="Link inválido ou expirado")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT reset_token_jti FROM utilizadores WHERE id = %s", (payload["sub"],))
        row = cursor.fetchone()
        if not row or row[0] is None or row[0] != payload.get("jti"):
            raise HTTPException(status_code=400, detail="Link inválido ou já foi utilizado")

        cursor.execute(
            "UPDATE utilizadores SET password = %s, reset_token_jti = NULL WHERE id = %s",
            (encriptar_password(dados.password_nova), payload["sub"])
        )
        conn.commit()
    finally:
        cursor.close()
        release_connection(conn)
    return {"ok": True}