from pydantic import BaseModel, EmailStr


class RegistoInput(BaseModel):
    nome:     str
    email:    EmailStr
    password: str

class LoginInput(BaseModel):
    email:    str
    password: str

class EsqueciPasswordInput(BaseModel):
    email: str

class RedefinirPasswordInput(BaseModel):
    token:         str
    password_nova: str