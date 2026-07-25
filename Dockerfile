FROM python:3.14-slim

WORKDIR /app

# psycopg2-binary já traz o driver compilado — não precisa de gcc/libpq-dev para build.
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY app/ ./app/
COPY scripts/ ./scripts/
COPY static/ ./static/

# não correr como root dentro do container — prática comum de endurecimento, sem custo
# nenhum aqui (a app não precisa de nenhum privilégio especial).
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Aplica migrações pendentes e só depois arranca o servidor — em produção a mesma
# ordem de sempre (ver README: createdb + python -m scripts.migrar + uvicorn).
CMD ["sh", "-c", "python -m scripts.migrar && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
