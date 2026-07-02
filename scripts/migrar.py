from pathlib import Path
import psycopg2
from app.core.config import settings

PASTA_MIGRACOES = Path(__file__).resolve().parent / "migrations"


def obter_conexao():
    return psycopg2.connect(
        host=settings.DB_HOST, port=settings.DB_PORT, dbname=settings.DB_NAME,
        user=settings.DB_USER, password=settings.DB_PASSWORD,
    )


def garantir_tabela_controlo(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migracoes (
            versao INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            aplicada_em TIMESTAMP DEFAULT now()
        )
    """)


def listar_migracoes_disponiveis():
    ficheiros = sorted(PASTA_MIGRACOES.glob("*.sql"))
    return [(int(f.name.split("_")[0]), f.name, f) for f in ficheiros]


def aplicar_migracoes():
    conn = obter_conexao()
    conn.autocommit = False
    cursor = conn.cursor()
    try:
        garantir_tabela_controlo(cursor)
        conn.commit()

        cursor.execute("SELECT versao FROM schema_migracoes")
        aplicadas = {row[0] for row in cursor.fetchall()}

        pendentes = [m for m in listar_migracoes_disponiveis() if m[0] not in aplicadas]
        if not pendentes:
            print("Nada para aplicar — schema já está atualizado.")
            return

        for versao, nome, caminho in pendentes:
            print(f"A aplicar {nome}...")
            cursor.execute(caminho.read_text(encoding="utf-8"))
            cursor.execute("SET search_path TO public")
            cursor.execute("INSERT INTO schema_migracoes (versao, nome) VALUES (%s, %s)", (versao, nome))
            conn.commit()
            print(f"  OK — {nome}")

        print(f"\n{len(pendentes)} migração(ões) aplicada(s).")
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    aplicar_migracoes()

# correr contra produção/desenvolvimento:
# python -m scripts.migrar