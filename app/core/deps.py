from datetime import datetime, timezone
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import verificar_token
from app.db.database import get_connection, release_connection

security = HTTPBearer()

def utilizador_atual(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verificar_token(credentials.credentials)
    if not payload or payload.get("tipo") == "reset":
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT sessoes_invalidadas_em FROM utilizadores WHERE id = %s", (payload["sub"],))
        row = cursor.fetchone()
    finally:
        cursor.close()
        release_connection(conn)

    if not row:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    invalidadas_em = row[0]
    if invalidadas_em and payload.get("iat"):
        iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        if invalidadas_em > iat:   # já não precisa de .replace(tzinfo=...)
            raise HTTPException(status_code=401, detail="Sessão terminada. Inicia sessão novamente.")

    return payload