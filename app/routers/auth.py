"""Registo, login e recuperação de password.

Tokens são JWT (ver app.core.security); a recuperação de password usa um token JWT à
parte, marcado com "tipo": "reset" e um jti de uso único guardado em
utilizadores.reset_token_jti.

As regras de negócio vivem em app.services.auth — este router trata da ligação à base de
dados e das partes que dependem de infra HTTP (rate limiting, emails em background).
"""

from datetime import timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from psycopg2.extras import RealDictCursor

from app.core.config import settings
from app.core.limiter import limiter
from app.core.security import criar_token
from app.db.database import get_db
from app.schemas.auth import (
    EsqueciPasswordInput,
    EsqueciPasswordOutput,
    LoginInput,
    RedefinirPasswordInput,
    RegistoInput,
    TokenOutput,
)
from app.schemas.comum import OkResponse
from app.services import auth as servico
from app.services.email import enviar_email

router = APIRouter(tags=["autenticação"])


@router.post("/registro", response_model=TokenOutput)
@limiter.limit("5/minute")
def registar(request: Request, dados: RegistoInput, cursor: RealDictCursor = Depends(get_db)):
    """Cria a conta, semeia a árvore de categorias por omissão, devolve um token de sessão."""
    utilizador_id = servico.criar_utilizador(cursor, cursor.connection, dados)
    token = criar_token({"sub": str(utilizador_id), "email": dados.email})
    return {"token": token, "nome": dados.nome}


@router.post("/login", response_model=TokenOutput)
@limiter.limit("5/minute")
def login(request: Request, dados: LoginInput, cursor: RealDictCursor = Depends(get_db)):
    """Autentica por email+password e devolve um token de sessão novo."""
    row = servico.autenticar(cursor, dados.email, dados.password)
    token = criar_token({"sub": str(row["id"]), "email": dados.email})
    return {"token": token, "nome": row["nome"]}


@router.post("/esqueci-password", response_model=EsqueciPasswordOutput)
@limiter.limit("3/hour")
def esqueci_password(
    request: Request, dados: EsqueciPasswordInput, background_tasks: BackgroundTasks,
    cursor: RealDictCursor = Depends(get_db),
):
    """Envia um link de reset por email — resposta idêntica exista ou não o email, de
    propósito, para não revelar quais emails estão registados."""
    resultado = servico.iniciar_reset_password(cursor, cursor.connection, dados.email)

    if resultado:
        token = criar_token({"sub": str(resultado["id"]), "tipo": "reset", "jti": resultado["jti"]}, timedelta(hours=1))
        link = f"{settings.BASE_URL}/static/index.html?token={token}"
        background_tasks.add_task(
            enviar_email, dados.email, "Recuperar password — Tesouraria",
            f"Clica neste link para definires uma password nova (válido por 1 hora):\n\n{link}"
        )
    return {"ok": True, "mensagem": "Se o email existir, enviámos instruções."}


@router.post("/redefinir-password", response_model=OkResponse)
@limiter.limit("5/minute")
def redefinir_password(request: Request, dados: RedefinirPasswordInput, cursor: RealDictCursor = Depends(get_db)):
    """Define a password nova a partir do token de reset (uso único, expira em 1 hora)."""
    servico.redefinir_password(cursor, cursor.connection, dados.token, dados.password_nova)
    return {"ok": True}
