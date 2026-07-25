"""Movimentos (transacções) — CRUD e o fluxo de confirmação da categorização automática.

As regras de negócio vivem em app.services.movimentos — este router só trata da ligação
à base de dados e da tradução HTTP <-> serviço.
"""

from fastapi import APIRouter, Depends
from psycopg2.extras import RealDictCursor

from app.core.deps import utilizador_atual
from app.db.database import get_db
from app.schemas.comum import OkResponse
from app.schemas.movimentos import ConfirmarTodosOutput, ContagemPendentesOutput, MovimentoInput, MovimentoOutput
from app.services import movimentos as servico

router = APIRouter(tags=["movimentos"])


@router.get("/movimentos", response_model=list[MovimentoOutput])
def listar_movimentos(
    utilizador: dict = Depends(utilizador_atual),
    cursor: RealDictCursor = Depends(get_db),
    conta_id: str | None = None,
    categoria_id: str | None = None,
    direcao: str | None = None,
    data_de: str | None = None,
    data_ate: str | None = None,
    precisa_confirmacao: bool | None = None,
    limit: int | None = None,
    offset: int = 0,
):
    """Lista movimentos com filtros; limit/offset são opcionais (sem eles devolve tudo)."""
    return servico.listar_movimentos(
        cursor, utilizador["sub"], conta_id, categoria_id, direcao,
        data_de, data_ate, precisa_confirmacao, limit, offset,
    )


@router.get("/movimentos/pendentes/contagem", response_model=ContagemPendentesOutput)
def contar_movimentos_pendentes(utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db)):
    """Quantos movimentos têm categorização automática por confirmar — banner de pendentes."""
    return servico.contar_movimentos_pendentes(cursor, utilizador["sub"])


@router.post("/movimentos", response_model=OkResponse)
def criar_movimento(dados: MovimentoInput, utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db)):
    """Cria um movimento manual (origem_cat='manual', já confirmado por definição)."""
    servico.criar_movimento(cursor, cursor.connection, utilizador["sub"], dados)
    return {"ok": True}


@router.put("/movimentos/{movimento_id}", response_model=OkResponse)
def editar_movimento(
    movimento_id: str, dados: MovimentoInput,
    utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db),
):
    """Edita um movimento; marca-o como confirmado e alimenta a cache de categorização."""
    servico.editar_movimento(cursor, cursor.connection, utilizador["sub"], movimento_id, dados)
    return {"ok": True}


@router.delete("/movimentos/{movimento_id}", response_model=OkResponse)
def eliminar_movimento(movimento_id: str, utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db)):
    """Elimina o movimento; não mexe na cache de categorização."""
    servico.eliminar_movimento(cursor, utilizador["sub"], movimento_id)
    return {"ok": True}


@router.post("/movimentos/{movimento_id}/confirmar", response_model=OkResponse)
def confirmar_movimento(movimento_id: str, utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db)):
    """Aceita a categoria sugerida (llm/sem_match → manual) e reforça a cache."""
    servico.confirmar_movimento(cursor, cursor.connection, utilizador["sub"], movimento_id)
    return {"ok": True}


@router.post("/movimentos/confirmar-todos", response_model=ConfirmarTodosOutput)
def confirmar_todos_os_pendentes(utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db)):
    """Confirma em massa todos os movimentos pendentes do utilizador."""
    return servico.confirmar_todos_os_pendentes(cursor, cursor.connection, utilizador["sub"])
