from pydantic import BaseModel


class StatsMensalOutput(BaseModel):
    mes:      str
    entradas: float
    saidas:   float
    liquido:  float

class StatsGrupoSubcategoriaOutput(BaseModel):
    categoria:      str
    categoria_id:   int
    categoria_slug: str | None
    total:          float
    n:              int

class StatsGrupoOutput(BaseModel):
    grupo:          str
    grupo_id:       int
    grupo_slug:     str | None
    eh_recebimento: bool
    total:          float
    subcategorias:  list[StatsGrupoSubcategoriaOutput]

class MesTotalOutput(BaseModel):
    mes:   str
    total: float

class MensalDetalheMesOutput(BaseModel):
    mes:        str
    # chave = nome da categoria-folha do grupo — dinâmico (depende das categorias que o
    # utilizador tem), por isso dict em vez de campos fixos; dict[str, float] em vez de um
    # `dict` genérico documenta pelo menos o tipo dos valores no /openapi.json.
    categorias: dict[str, float]

class MensalDetalheGrupoOutput(BaseModel):
    meses:            list[MensalDetalheMesOutput]
    categorias:       list[str]
    # slugs alinhados por índice com `categorias` (mesmo nome pode ter slug None se a
    # categoria foi criada pelo utilizador) — permite ao frontend traduzir os nomes.
    categorias_slugs: list[str | None]

class SaldoDiarioOutput(BaseModel):
    data:  str
    saldo: float

class RecorrenteOutput(BaseModel):
    descricao:             str
    categoria:             str
    categoria_slug:        str | None
    grupo:                 str
    grupo_slug:            str | None
    ocorrencias:           int
    valor_medio:           float
    ultima_vez:            str
    intervalo_medio_dias:  int
    proxima_data_estimada: str
    regular:               bool
