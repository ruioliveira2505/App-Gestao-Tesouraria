"""Estatísticas e agregações sobre movimentos — tudo somente-leitura.

As regras de negócio vivem em app.services.estatisticas — este router só trata da ligação
à base de dados e da tradução HTTP <-> serviço.
"""

from fastapi import APIRouter, Depends
from psycopg2.extras import RealDictCursor

from app.core.deps import utilizador_atual
from app.db.database import get_db
from app.schemas.estatisticas import (
    MensalDetalheGrupoOutput,
    MesTotalOutput,
    RecorrenteOutput,
    SaldoDiarioOutput,
    StatsGrupoOutput,
    StatsMensalOutput,
)
from app.services import estatisticas as servico

router = APIRouter(tags=["estatísticas"])


@router.get("/stats/mensal", response_model=list[StatsMensalOutput])
def stats_mensal(
    utilizador: dict = Depends(utilizador_atual),
    cursor: RealDictCursor = Depends(get_db),
    conta_id: str | None = None, tipo: str | None = None,
    data_de: str | None = None, data_ate: str | None = None,
    excluir_categorias: str | None = None,
):
    """Entradas/saídas/líquido agregados por mês."""
    return servico.stats_mensal(cursor, utilizador["sub"], conta_id, tipo, data_de, data_ate, excluir_categorias)


@router.get("/stats/grupos", response_model=list[StatsGrupoOutput])
def stats_grupos(
    utilizador: dict = Depends(utilizador_atual),
    cursor: RealDictCursor = Depends(get_db),
    conta_id: str | None = None, tipo: str | None = None,
    data_de: str | None = None, data_ate: str | None = None,
    excluir_categorias: str | None = None,
):
    """Total por grupo, com as categorias-folha de cada grupo listadas dentro dele."""
    return servico.stats_grupos(cursor, utilizador["sub"], conta_id, tipo, data_de, data_ate, excluir_categorias)


@router.get("/stats/mensal-detalhe", response_model=list[MesTotalOutput] | MensalDetalheGrupoOutput)
def stats_mensal_detalhe(
    utilizador: dict = Depends(utilizador_atual),
    cursor: RealDictCursor = Depends(get_db),
    grupo_id: int | None = None, categoria_id: int | None = None,
    conta_id: str | None = None, tipo: str | None = None,
    data_de: str | None = None, data_ate: str | None = None,
    excluir_categorias: str | None = None,
):
    """Evolução mensal de uma categoria (lista mes+total), ou de um grupo (objecto
    meses+categorias, com as categorias separadas) — a forma da resposta depende de qual
    parâmetro é passado. grupo_id e categoria_id são mutuamente exclusivos."""
    return servico.stats_mensal_detalhe(
        cursor, utilizador["sub"], grupo_id, categoria_id, conta_id, tipo, data_de, data_ate, excluir_categorias
    )


@router.get("/stats/saldo-diario", response_model=list[SaldoDiarioOutput])
def stats_saldo_diario(
    utilizador: dict = Depends(utilizador_atual),
    cursor: RealDictCursor = Depends(get_db),
    conta_id: str | None = None, tipo: str | None = None,
    data_de: str | None = None, data_ate: str | None = None,
):
    """Saldo total (das contas filtradas) dia a dia, desde a âncora mais antiga até hoje."""
    return servico.stats_saldo_diario(cursor, utilizador["sub"], conta_id, tipo, data_de, data_ate)


@router.get("/stats/recorrentes", response_model=list[RecorrenteOutput])
def stats_recorrentes(
    utilizador: dict = Depends(utilizador_atual),
    cursor: RealDictCursor = Depends(get_db),
    conta_id: str | None = None, tipo: str | None = None,
    data_de: str | None = None, data_ate: str | None = None,
    excluir_categorias: str | None = None,
):
    """Deteta despesas que se repetem (mesma descrição+categoria, ≥2 ocorrências) e estima
    a próxima data — "regular" quando o desvio-padrão dos intervalos é < 40% da média."""
    return servico.stats_recorrentes(cursor, utilizador["sub"], conta_id, tipo, data_de, data_ate, excluir_categorias)
