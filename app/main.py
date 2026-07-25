import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.dominio import ErroDominio
from app.core.errors import erro_dominio_handler, validation_exception_handler
from app.core.limiter import limiter
from app.db.database import get_connection, release_connection
from app.routers import auth, categorias, contas, estatisticas, movimentos, perfil

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="Tesouraria",
    description="API de gestão de finanças pessoais — contas, movimentos, categorias e "
                 "reconciliações de saldo.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.BASE_URL],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ErroDominio, erro_dominio_handler)

PASTA_STATIC = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=PASTA_STATIC), name="static")

app.include_router(auth.router)
app.include_router(perfil.router)
app.include_router(contas.router)
app.include_router(categorias.router)
app.include_router(movimentos.router)
app.include_router(estatisticas.router)


@app.get("/", tags=["sistema"])
def raiz():
    """Ping simples — confirma que a API está no ar."""
    return {"status": "ok", "projeto": "tesouraria"}


@app.get("/health", tags=["sistema"])
def health():
    """Estado da API e da ligação à base de dados — usar para health checks de deploy."""
    try:
        conn = get_connection()
        release_connection(conn)
        return {"status": "ok", "database": "ok"}
    except Exception:
        return {"status": "degraded", "database": "unreachable"}

# arrancar servidor
# uvicorn app.main:app --reload
# http://localhost:8000/static/index.html