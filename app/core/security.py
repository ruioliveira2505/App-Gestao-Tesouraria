from datetime import datetime, timedelta, timezone
import jwt
from jwt import PyJWTError
import bcrypt

from app.core.config import settings


def encriptar_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verificar_password(password: str, hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hash.encode("utf-8"))


def criar_token(dados: dict, validade: timedelta = None) -> str:
    payload = dados.copy()
    payload["exp"] = datetime.now(timezone.utc) + (validade or timedelta(days=settings.TOKEN_DIAS))
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITMO_JWT)


def verificar_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITMO_JWT])
    except PyJWTError:
        return None