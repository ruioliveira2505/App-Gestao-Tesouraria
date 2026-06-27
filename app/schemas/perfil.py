from pydantic import BaseModel, EmailStr, Field

class PerfilUpdateInput(BaseModel):
    nome:  str
    email: EmailStr

class PasswordUpdateInput(BaseModel):
    password_atual: str
    password_nova:  str = Field(min_length=8)