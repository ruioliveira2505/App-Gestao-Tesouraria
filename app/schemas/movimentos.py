from datetime import date

from pydantic import BaseModel, Field


class MovimentoInput(BaseModel):
    conta_id:     str
    data:         date
    descricao:    str = Field(min_length=1, max_length=255)
    valor:        float
    categoria_id: int


class MovimentoOutput(BaseModel):
    id:            str
    conta_id:      str
    data:          str
    descricao:     str
    valor:         float
    categoria_id:  int
    categoria:     str
    categoria_slug: str | None
    grupo:         str
    grupo_slug:    str | None
    origem_cat:    str
    confirmado:    bool
    sem_categoria: bool

class ContagemPendentesOutput(BaseModel):
    contagem: int

class ConfirmarTodosOutput(BaseModel):
    ok:          bool = True
    confirmados: int