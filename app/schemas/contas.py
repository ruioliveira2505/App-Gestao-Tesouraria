from pydantic import BaseModel


class ContaInput(BaseModel):
    nome:  str
    banco: str
    tipo:  str
    iban:  str
    moeda: str
    saldo: float

class ContaEditInput(BaseModel):
    nome:  str
    banco: str
    tipo:  str
    iban:  str
    moeda: str

class AjusteSaldoCriarInput(BaseModel):
    data:       str
    saldo_real: float

class AjusteSaldoEditarInput(BaseModel):
    data:       str
    saldo_real: float