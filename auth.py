from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "muda-isto-para-algo-secreto")
ALGORITMO  = "HS256"
TOKEN_DIAS = 30

def encriptar_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verificar_password(password: str, hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hash.encode("utf-8"))

def criar_token(dados: dict, validade: timedelta = None) -> str:
    payload = dados.copy()
    payload["exp"] = datetime.utcnow() + (validade or timedelta(days=TOKEN_DIAS))
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITMO)

def verificar_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITMO])
    except JWTError:
        return None