import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.limiter import limiter
from app.core.errors import validation_exception_handler
from app.db.database import get_connection, release_connection, release_connection
from app.routers import auth, perfil, contas, categorias, movimentos, stats

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.BASE_URL],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(perfil.router)
app.include_router(contas.router)
app.include_router(categorias.router)
app.include_router(movimentos.router)
app.include_router(stats.router)


@app.get("/")
def raiz():
    return {"status": "ok", "projeto": "tesouraria"}


@app.get("/health")
def health():
    try:
        conn = get_connection()
        release_connection(conn)
        return {"status": "ok", "database": "ok"}
    except Exception:
        return {"status": "degraded", "database": "unreachable"}

# arrancar servidor
# uvicorn app.main:app --reload
# http://localhost:8000/static/index.html