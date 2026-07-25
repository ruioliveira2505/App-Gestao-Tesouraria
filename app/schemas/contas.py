from datetime import date

from pydantic import BaseModel, Field


class ContaInput(BaseModel):
    nome:  str = Field(min_length=1, max_length=120)
    banco: str | None = Field(default=None, max_length=120)
    tipo:  str | None = Field(default=None, max_length=40)
    iban:  str | None = Field(default=None, max_length=34)
    moeda: str = Field(min_length=1, max_length=10)
    saldo: float
    data:  date

class ContaEditInput(BaseModel):
    nome:  str = Field(min_length=1, max_length=120)
    banco: str | None = Field(default=None, max_length=120)
    tipo:  str | None = Field(default=None, max_length=40)
    iban:  str | None = Field(default=None, max_length=34)
    moeda: str = Field(min_length=1, max_length=10)

class AjusteSaldoInput(BaseModel):
    data:       date
    saldo_real: float


class ContaOutput(BaseModel):
    id:     str
    nome:   str
    banco:  str | None
    iban:   str | None
    moeda:  str
    tipo:   str | None
    inicio: str
    saldo:  float

class InicioContaOutput(BaseModel):
    data:       str
    saldo_real: float

class SaldoOutput(BaseModel):
    saldo: float

class AjusteSaldoOutput(BaseModel):
    id:          int
    data:        str
    saldo_real:  float
    saldo_antes: float
