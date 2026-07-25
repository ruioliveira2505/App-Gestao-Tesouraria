"""Regras de negócio de registo, login e recuperação de password.

Cada função recebe um cursor já aberto (a ligação/transacção é gerida pelo router) e
levanta ErroDominio para qualquer regra violada — não sabe o que é HTTP. A construção do
token JWT de sessão e o envio de email ficam no router, porque dependem de infra HTTP
(BackgroundTasks, settings.BASE_URL) — aqui só entram a validação e o acesso a dados.
"""

import uuid

import psycopg2
from psycopg2.extensions import connection as PgConnection
from psycopg2.extras import RealDictCursor

from app.core.dominio import ErroDominio
from app.core.security import encriptar_password, verificar_password, verificar_token
from app.schemas.auth import RegistoInput
from app.services.categorias_seed import seed_categorias_padrao

# hash fixo (não corresponde a nenhuma password real) só para gastar o mesmo tempo de
# bcrypt quando o email não existe — evita que o tempo de resposta do /login denuncie
# se um email está ou não registado.
_HASH_DUMMY = encriptar_password("dummy-password-para-igualar-tempo-de-resposta")


def criar_utilizador(cursor: RealDictCursor, conn: PgConnection, dados: RegistoInput) -> int:
    """Cria a conta e semeia a árvore de categorias por omissão — tudo na mesma
    transacção: se o seed falhar a meio, a conta recém-criada é revertida também, em vez
    de ficar uma conta órfã (sem categorias) com o email já ocupado para sempre. O commit
    fica a cargo de quem chamar (o router, via get_db) só depois de tudo correr bem."""
    cursor.execute("SELECT id FROM utilizadores WHERE email = %s", (dados.email,))
    if cursor.fetchone():
        raise ErroDominio(400, "EMAIL_JA_REGISTADO", "Email já registado")

    hash_pw = encriptar_password(dados.password)
    try:
        cursor.execute(
            "INSERT INTO utilizadores (nome, email, password) VALUES (%s, %s, %s) RETURNING id",
            (dados.nome, dados.email, hash_pw)
        )
    except psycopg2.errors.UniqueViolation:
        # corrida rara: dois registos com o mesmo email a passar a verificação SELECT
        # acima ao mesmo tempo — o UNIQUE constraint apanha na mesma, só não com a
        # mensagem certa sem isto.
        conn.rollback()
        raise ErroDominio(400, "EMAIL_JA_REGISTADO", "Email já registado") from None

    utilizador_id = cursor.fetchone()["id"]
    seed_categorias_padrao(cursor, utilizador_id)
    return utilizador_id


def autenticar(cursor: RealDictCursor, email: str, password: str) -> dict:
    """Verifica email+password; usa um hash dummy quando o email não existe para que o
    tempo de resposta não denuncie se um email está ou não registado."""
    cursor.execute("SELECT id, nome, password FROM utilizadores WHERE email = %s", (email,))
    row = cursor.fetchone()

    hash_para_verificar = row["password"] if row else _HASH_DUMMY
    password_correta = verificar_password(password, hash_para_verificar)
    if not row or not password_correta:
        raise ErroDominio(401, "CREDENCIAIS_INVALIDAS", "Email ou password incorretos")
    return row


def iniciar_reset_password(cursor: RealDictCursor, conn: PgConnection, email: str) -> dict | None:
    """Se o email existir, gera e grava um jti de uso único para o token de reset.
    Devolve None se não existir — o router responde a mesma coisa em ambos os casos,
    de propósito, para não revelar quais emails estão registados."""
    cursor.execute("SELECT id FROM utilizadores WHERE email = %s", (email,))
    row = cursor.fetchone()
    if not row:
        return None

    jti = str(uuid.uuid4())
    cursor.execute("UPDATE utilizadores SET reset_token_jti = %s WHERE id = %s", (jti, row["id"]))
    conn.commit()
    return {"id": row["id"], "jti": jti}


def redefinir_password(cursor: RealDictCursor, conn: PgConnection, token: str, password_nova: str) -> None:
    """Define a password nova a partir do token de reset; invalida todas as sessões
    activas e o próprio token de reset (uso único, via reset_token_jti)."""
    payload = verificar_token(token)
    if not payload or payload.get("tipo") != "reset":
        raise ErroDominio(400, "TOKEN_INVALIDO", "Link inválido ou expirado")

    cursor.execute("SELECT reset_token_jti FROM utilizadores WHERE id = %s", (payload["sub"],))
    row = cursor.fetchone()
    if not row or row["reset_token_jti"] is None or row["reset_token_jti"] != payload.get("jti"):
        raise ErroDominio(400, "TOKEN_JA_UTILIZADO", "Link inválido ou já foi utilizado")

    cursor.execute(
        "UPDATE utilizadores SET password = %s, reset_token_jti = NULL, sessoes_invalidadas_em = now() WHERE id = %s",
        (encriptar_password(password_nova), payload["sub"])
    )
    conn.commit()
