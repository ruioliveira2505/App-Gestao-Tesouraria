"""Categorias — árvore de dois níveis (grupo → categoria-folha) numa só tabela.

Um "grupo" é uma linha com parent_id NULL; uma "categoria-folha" tem parent_id apontado
para o grupo. Categorias marcadas como protegidas fazem parte do sistema (ex: o fallback
"Outros") e não podem ser editadas nem eliminadas.

As regras de negócio vivem em app.services.categorias — este router só trata da ligação
à base de dados e da tradução HTTP <-> serviço.
"""

from fastapi import APIRouter, Depends
from psycopg2.extras import RealDictCursor

from app.core.deps import utilizador_atual
from app.db.database import get_db
from app.schemas.categorias import ArvoreGrupoOutput, CategoriaGestaoInput, CategoriaOutput, ReordenarCategoriasInput
from app.schemas.comum import OkResponse
from app.services import categorias as servico

router = APIRouter(tags=["categorias"])


@router.get("/categorias", response_model=list[CategoriaOutput])
def listar_categorias(utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db)):
    """Lista só as categorias-folha, cada uma com o nome do grupo a que pertence."""
    return servico.listar_categorias(cursor, utilizador["sub"])


@router.get("/categorias/arvore", response_model=list[ArvoreGrupoOutput])
def arvore_categorias(utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db)):
    """Grupos com as respectivas categorias-folha aninhadas — usado nos selectores da UI."""
    return servico.listar_arvore(cursor, utilizador["sub"])


@router.post("/categorias", response_model=OkResponse)
def criar_categoria(dados: CategoriaGestaoInput, utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db)):
    """Cria um grupo (sem parent_id) ou uma categoria-folha (com parent_id)."""
    servico.criar_categoria(cursor, utilizador["sub"], dados)
    return {"ok": True}


@router.put("/categorias/reordenar", response_model=OkResponse)
def reordenar_categorias(dados: ReordenarCategoriasInput, utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db)):
    """Grava a nova ordem (lista de ids) — usado no arrastar-e-largar."""
    servico.reordenar(cursor, utilizador["sub"], dados.ids)
    return {"ok": True}


@router.put("/categorias/{categoria_id}", response_model=OkResponse)
def editar_categoria(
    categoria_id: int, dados: CategoriaGestaoInput,
    utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db),
):
    """Renomeia e/ou move uma categoria-folha para outro grupo; categorias protegidas
    não podem ser editadas."""
    servico.editar_categoria(cursor, utilizador["sub"], categoria_id, dados)
    return {"ok": True}


@router.delete("/categorias/{categoria_id}", response_model=OkResponse)
def eliminar_categoria(
    categoria_id: int, migrar_para_id: int | None = None, forcar: bool = False,
    utilizador: dict = Depends(utilizador_atual), cursor: RealDictCursor = Depends(get_db),
):
    """Elimina um grupo ou categoria-folha; migrar_para_id/forcar tratam do que fazer aos
    movimentos (ou subcategorias) que ainda lá estejam."""
    servico.eliminar_categoria(cursor, utilizador["sub"], categoria_id, migrar_para_id, forcar)
    return {"ok": True}
