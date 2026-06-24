import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Base de dados
    DB_HOST     = os.getenv("DB_HOST")
    DB_PORT     = os.getenv("DB_PORT")
    DB_NAME     = os.getenv("DB_NAME")
    DB_USER     = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    # Autenticação
    SECRET_KEY    = os.getenv("SECRET_KEY")
    ALGORITMO_JWT = os.getenv("ALGORITMO_JWT", "HS256")
    TOKEN_DIAS    = int(os.getenv("TOKEN_DIAS", "30"))

    # Email
    EMAIL_REMETENTE    = os.getenv("EMAIL_REMETENTE")
    EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

    # Categorização (LLM)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # URL pública (CORS + links de email) — único sítio a mudar quando fizeres deploy
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

    def __init__(self):
        if not self.SECRET_KEY:
            raise RuntimeError(
                "SECRET_KEY não está definida no .env. A aplicação não arranca sem ela "
                "(o valor por defeito inseguro foi removido propositadamente)."
            )


settings = Settings()