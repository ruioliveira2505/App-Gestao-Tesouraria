from pydantic import BaseModel, EmailStr, Field


class PerfilUpdateInput(BaseModel):
    nome:  str = Field(min_length=1, max_length=120)
    email: EmailStr

class PasswordUpdateInput(BaseModel):
    password_atual: str
    password_nova: str = Field(min_length=8, max_length=72)


class PerfilOutput(BaseModel):
    id:    str
    nome:  str
    email: str

class AtualizarPerfilOutput(BaseModel):
    ok:   bool = True
    nome: str

class PasswordUpdateOutput(BaseModel):
    ok:    bool = True
    token: str