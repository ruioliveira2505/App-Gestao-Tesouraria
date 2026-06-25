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

class AjusteSaldoInput(BaseModel):
    data:       str
    saldo_real: float
