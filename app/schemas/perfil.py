from pydantic import BaseModel, EmailStr


class PerfilUpdateInput(BaseModel):
    nome:  str
    email: EmailStr

class PasswordUpdateInput(BaseModel):
    password_atual: str
    password_nova:  str