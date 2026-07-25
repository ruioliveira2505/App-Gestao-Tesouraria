from pydantic import BaseModel, Field


class CategoriaGestaoInput(BaseModel):
    nome:           str = Field(min_length=1, max_length=80)
    parent_id:      int  | None = None
    eh_recebimento: bool | None = None

class ReordenarCategoriasInput(BaseModel):
    ids: list[int]


class CategoriaOutput(BaseModel):
    id:             int
    nome:           str
    grupo:          str
    eh_recebimento: bool
    # slug estável (ex. "out.alimentacao.supermercado") para o i18n do frontend traduzir o
    # nome sem depender do texto actual — None nas categorias criadas pelo utilizador.
    slug:           str | None

class ArvoreFolhaOutput(BaseModel):
    id:        int
    nome:      str
    protegida: bool
    slug:      str | None

class ArvoreGrupoOutput(BaseModel):
    id:             int
    nome:           str
    eh_recebimento: bool
    slug:           str | None
    categorias:     list[ArvoreFolhaOutput]