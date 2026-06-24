from pydantic import BaseModel


class MovimentoInput(BaseModel):
    conta_id:     str
    data:         str
    descricao:    str
    valor:        float
    categoria_id: int