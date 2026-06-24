import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

def testar_conexao():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        versao = cursor.fetchone()
        print(f"Ligado ao PostgreSQL: {versao[0]}")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao ligar: {e}")

if __name__ == "__main__":
    testar_conexao()