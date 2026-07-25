from pydantic import BaseModel, EmailStr, Field


class RegistoInput(BaseModel):
    nome:     str = Field(min_length=1, max_length=120)
    email:    EmailStr
    password: str = Field(min_length=8, max_length=72)

class LoginInput(BaseModel):
    email:    EmailStr
    password: str

class EsqueciPasswordInput(BaseModel):
    email: EmailStr

class RedefinirPasswordInput(BaseModel):
    token:         str
    password_nova: str = Field(min_length=8, max_length=72)


class TokenOutput(BaseModel):
    token: str
    nome:  str

class EsqueciPasswordOutput(BaseModel):
    ok:       bool = True
    mensagem: str