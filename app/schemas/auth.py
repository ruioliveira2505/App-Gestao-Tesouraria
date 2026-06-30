from pydantic import BaseModel, EmailStr, Field

class RegistoInput(BaseModel):
    nome:     str
    email:    EmailStr
    password: str = Field(min_length=8, max_length=72)

class LoginInput(BaseModel):
    email:    str
    password: str

class EsqueciPasswordInput(BaseModel):
    email: str

class RedefinirPasswordInput(BaseModel):
    token:         str
    password_nova: str = Field(min_length=8, max_length=72)