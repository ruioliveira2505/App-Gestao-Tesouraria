from pydantic import BaseModel


class ContaInput(BaseModel):
    nome:  str
    banco: str | None = None
    tipo:  str | None = None
    iban:  str | None = None
    moeda: str
    saldo: float

class ContaEditInput(BaseModel):
    nome:  str
    banco: str | None = None
    tipo:  str | None = None
    iban:  str | None = None
    moeda: str

class AjusteSaldoInput(BaseModel):
    data:       str
    saldo_real: float
