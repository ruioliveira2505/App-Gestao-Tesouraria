from datetime import UTC, datetime

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from psycopg2.extras import RealDictCursor

from app.core.errors import erro_http
from app.core.security import verificar_token
from app.db.database import get_db

security = HTTPBearer()

def utilizador_atual(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    cursor: RealDictCursor = Depends(get_db),
) -> dict:
    """Também depende de get_db — como o FastAPI só resolve get_db uma vez por pedido
    (cache por omissão do Depends), esta verificação de sessão e o resto do pedido acabam
    a partilhar a mesma ligação/cursor, em vez de abrirem uma ligação à parte cada um."""
    payload = verificar_token(credentials.credentials)
    if not payload or payload.get("tipo") == "reset":
        raise erro_http(401, "TOKEN_INVALIDO", "Token inválido ou expirado")

    cursor.execute("SELECT sessoes_invalidadas_em FROM utilizadores WHERE id = %s", (payload["sub"],))
    row = cursor.fetchone()

    if not row:
        raise erro_http(401, "TOKEN_INVALIDO", "Token inválido ou expirado")

    invalidadas_em = row["sessoes_invalidadas_em"]
    if invalidadas_em and payload.get("iat"):
        iat = datetime.fromtimestamp(payload["iat"], tz=UTC)
        if invalidadas_em > iat:   # já não precisa de .replace(tzinfo=...)
            raise erro_http(401, "SESSAO_TERMINADA", "Sessão terminada. Inicia sessão novamente.")

    return payload