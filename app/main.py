from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.limiter import limiter
from app.routers import auth, perfil, contas, categorias, movimentos, stats

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.BASE_URL],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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

# arrancar servidor
# uvicorn app.main:app --reload
# http://localhost:8000/static/index.html