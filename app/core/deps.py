from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import verificar_token

security = HTTPBearer()


def utilizador_atual(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verificar_token(credentials.credentials)
    if not payload or payload.get("tipo") == "reset":
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    return payload