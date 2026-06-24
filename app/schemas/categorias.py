from pydantic import BaseModel


class CategoriaGestaoInput(BaseModel):
    nome:           str
    parent_id:      int  | None = None
    eh_recebimento: bool | None = None