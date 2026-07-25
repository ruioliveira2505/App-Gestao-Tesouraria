"""Contas, reconciliações e a âncora de saldo inicial.

Conceito central: cada conta tem uma "âncora" (data_ancora/saldo_ancora, colunas próprias
de `contas` — ver ARCHITECTURE.md) que representa o saldo antes de qualquer movimento. É
editada à parte (/contas/{id}/inicio), nunca aparece em GET /contas/{id}/ajustes-saldo, e
por isso tem regras próprias de validação — ver a secção "Data de Início de Movimentos"
mais abaixo.

As regras de negócio vivem em app.services.contas — este router só trata da ligação à
base de dados e da tradução HTTP <-> serviço.
"""

from datetime import date

from fastapi import APIRouter, Depends
from psycopg2.extras import RealDictCursor

from app.core.deps import utilizador_atual
from app.db.database import get_db
from app.schemas.comum import OkResponse
from app.schemas.contas import (
    AjusteSaldoInput,
    AjusteSaldoOutput,
    ContaEditInput,
    ContaInput,
    ContaOutput,
    InicioContaOutput,
    SaldoOutput,
)
from app.services import contas as servico

router = APIRouter(tags=["contas"])


# ─── contas ───────────────────────────────────────────────────────────────────

@router.get("/contas", response_model=list[ContaOutput])
def listar_contas(utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db)):
    """Lista as contas do utilizador com o saldo actual já calculado."""
    return servico.listar_contas(cursor, utilizador["sub"])


@router.post("/contas", response_model=OkResponse)
def criar_conta(dados: ContaInput, utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db)):
    """Cria a conta e a sua âncora de saldo inicial."""
    servico.criar_conta(cursor, utilizador["sub"], dados)
    return {"ok": True}


@router.put("/contas/{conta_id}", response_model=OkResponse)
def editar_conta(
    conta_id: str, dados: ContaEditInput,
    utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db),
):
    """Actualiza os dados descritivos da conta — não mexe em saldo nem na âncora."""
    servico.editar_conta(cursor, utilizador["sub"], conta_id, dados)
    return {"ok": True}


@router.delete("/contas/{conta_id}", response_model=OkResponse)
def eliminar_conta(
    conta_id: str, forcar: bool = False,
    utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db),
):
    """Elimina a conta; se tiver movimentos, exige forcar=true (elimina-os também)."""
    servico.eliminar_conta(cursor, utilizador["sub"], conta_id, forcar)
    return {"ok": True}


# ─── Data de Início de Movimentos / Saldo Inicial (a âncora da conta) ────────

@router.get("/contas/{conta_id}/inicio", response_model=InicioContaOutput)
def obter_inicio_conta(conta_id: str, utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db)):
    """Devolve a Data de Início de Movimentos e o saldo da âncora (âncora + 1 dia)."""
    return servico.obter_inicio_conta(cursor, utilizador["sub"], conta_id)


@router.put("/contas/{conta_id}/inicio", response_model=OkResponse)
def editar_inicio_conta(
    conta_id: str,
    dados: AjusteSaldoInput,
    confirmar: bool = False,
    utilizador: dict = Depends(utilizador_atual),
    cursor: RealDictCursor = Depends(get_db),
):
    """Move a Data de Início de Movimentos (recua ou avança a âncora)."""
    servico.editar_inicio_conta(cursor, utilizador["sub"], conta_id, dados, confirmar)
    return {"ok": True}


# ─── ajustes de saldo (reconciliações — nunca inclui a âncora, ver acima) ────

@router.get("/contas/{conta_id}/saldo-em-data", response_model=SaldoOutput)
def saldo_em_data(conta_id: str, data: date, utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db)):
    """Saldo da conta numa data específica (âncora/reconciliação anterior + movimentos)."""
    return servico.saldo_em_data(cursor, utilizador["sub"], conta_id, data)


@router.get("/contas/{conta_id}/ajustes-saldo", response_model=list[AjusteSaldoOutput])
def listar_ajustes_saldo(conta_id: str, utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db)):
    """Lista as reconciliações da conta (nunca inclui a âncora)."""
    return servico.listar_ajustes_saldo(cursor, utilizador["sub"], conta_id)


@router.post("/contas/{conta_id}/ajustes-saldo", response_model=OkResponse)
def criar_ajuste_saldo(
    conta_id: str, dados: AjusteSaldoInput,
    utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db),
):
    """Cria uma reconciliação nova — a data tem de ser posterior à âncora."""
    servico.criar_ajuste_saldo(cursor, cursor.connection, utilizador["sub"], conta_id, dados)
    return {"ok": True}


@router.put("/ajustes-saldo/{ajuste_id}", response_model=OkResponse)
def editar_ajuste_saldo(
    ajuste_id: int, dados: AjusteSaldoInput,
    utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db),
):
    """Corrige o saldo de uma reconciliação — a data nunca é editável."""
    servico.editar_ajuste_saldo(cursor, utilizador["sub"], ajuste_id, dados)
    return {"ok": True}


@router.delete("/ajustes-saldo/{ajuste_id}", response_model=OkResponse)
def eliminar_ajuste_saldo(ajuste_id: int, utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db)):
    """Elimina uma reconciliação."""
    servico.eliminar_ajuste_saldo(cursor, utilizador["sub"], ajuste_id)
    return {"ok": True}
