from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from jwt import PyJWTError

from app.core.config import settings


def encriptar_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verificar_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def criar_token(dados: dict, validade: timedelta | None = None) -> str:
    payload = dados.copy()
    agora = datetime.now(UTC)
    # iat como float (não datetime) para não perder precisão de microssegundos —
    # o PyJWT trunca datetimes para segundos inteiros, o que faz um token novo
    # nascer já invalidado se sessoes_invalidadas_em (timestamptz, com microssegundos)
    # for gravado no mesmo segundo em que o token é emitido.
    payload["iat"] = agora.timestamp()
    payload["exp"] = agora + (validade or timedelta(days=settings.TOKEN_DIAS))
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITMO_JWT)

def verificar_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITMO_JWT])
    except PyJWTError:
        return None