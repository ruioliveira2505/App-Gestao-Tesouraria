from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuração da app, lida do .env (ou do ambiente, que tem prioridade sobre o
    ficheiro). Campos sem valor por omissão são obrigatórios — a app falha logo no
    arranque, com uma mensagem a listar tudo o que falta de uma vez, em vez de rebentar
    mais tarde (e de forma menos clara) quando algo tentar usar um valor em falta."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Base de dados — sem valor por omissão: a app não funciona sem ligação à BD.
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    # Autenticação — sem valor por omissão de propósito, não faz sentido ter uma
    # SECRET_KEY insegura como fallback. min_length=32 não garante entropia a sério (uma
    # string de 32 "a"s passa), mas trava o caso mais comum — copiar um valor de exemplo
    # curto tipo "changeme" ou "segredo123" sem substituir por uma chave gerada a sério
    # (ver README: `python -c "import secrets; print(secrets.token_hex(32))"`, 64 chars).
    SECRET_KEY: str = Field(min_length=32)
    ALGORITMO_JWT: str = "HS256"
    TOKEN_DIAS: int = 30

    # Email (recuperação de password) — opcional: sem isto a app arranca à mesma, só falha
    # quando alguém pedir de facto um email (ver enviar_email, app/services/email.py).
    # EMAIL_SMTP_HOST/PORT têm por omissão o Gmail (o único usado até hoje) — só é preciso
    # definir no .env se um dia se trocar de fornecedor de email.
    EMAIL_REMETENTE: str | None = None
    EMAIL_APP_PASSWORD: str | None = None
    EMAIL_SMTP_HOST: str = "smtp.gmail.com"
    EMAIL_SMTP_PORT: int = 465

    # Categorização automática (LLM via Groq) — opcional, cai sempre no fallback sem isto.
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # URL pública (CORS + links de email) — único sítio a mudar quando fizeres deploy
    BASE_URL: str = "http://localhost:8000"


settings = Settings()
