"""Perfil do utilizador autenticado — dados de conta, password e sessões.

As regras de negócio vivem em app.services.perfil — este router só trata da ligação à
base de dados e da tradução HTTP <-> serviço.
"""

from fastapi import APIRouter, Depends, Request
from psycopg2.extras import RealDictCursor

from app.core.deps import utilizador_atual
from app.core.limiter import limiter
from app.core.security import criar_token
from app.db.database import get_db
from app.schemas.comum import OkResponse
from app.schemas.perfil import AtualizarPerfilOutput, PasswordUpdateInput, PasswordUpdateOutput, PerfilOutput, PerfilUpdateInput
from app.services import perfil as servico

router = APIRouter(tags=["perfil"])


@router.get("/me", response_model=PerfilOutput)
def perfil(utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db)):
    """Dados do utilizador autenticado (id, nome, email)."""
    return servico.obter_perfil(cursor, utilizador["sub"])


@router.put("/me", response_model=AtualizarPerfilOutput)
def atualizar_perfil(dados: PerfilUpdateInput, utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db)):
    """Actualiza nome e/ou email."""
    servico.atualizar_perfil(cursor, utilizador["sub"], dados)
    return {"ok": True, "nome": dados.nome}


@router.put("/me/password", response_model=PasswordUpdateOutput)
@limiter.limit("5/minute")
def atualizar_password(
    request: Request, dados: PasswordUpdateInput,
    utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db),
):
    """Muda a password e invalida sessões anteriores; devolve um token novo já válido."""
    email = servico.atualizar_password(cursor, utilizador["sub"], dados)
    novo_token = criar_token({"sub": utilizador["sub"], "email": email})
    return {"ok": True, "token": novo_token}


@router.post("/me/sessoes/terminar", response_model=OkResponse)
def terminar_todas_as_sessoes(utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db)):
    """Invalida todos os tokens emitidos até agora, incluindo o usado neste pedido."""
    servico.terminar_todas_as_sessoes(cursor, utilizador["sub"])
    return {"ok": True}


@router.delete("/me", response_model=OkResponse)
def eliminar_conta_utilizador(utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db)):
    """Elimina a conta e todos os dados associados (contas, movimentos, categorias)."""
    servico.eliminar_conta_utilizador(cursor, utilizador["sub"])
    return {"ok": True}
