"""Regras de negócio do perfil do utilizador autenticado — dados de conta, password e
sessões.

Cada função recebe um cursor já aberto (a ligação/transacção é gerida pelo router) e
levanta ErroDominio para qualquer regra violada — não sabe o que é HTTP.
"""

from psycopg2.extras import RealDictCursor

from app.core.dominio import ErroDominio
from app.core.security import encriptar_password, verificar_password
from app.schemas.perfil import PasswordUpdateInput, PerfilUpdateInput


def obter_perfil(cursor: RealDictCursor, uid: str) -> dict:
    cursor.execute("SELECT nome, email FROM utilizadores WHERE id=%s", (uid,))
    row = cursor.fetchone()
    return {"email": row["email"], "id": uid, "nome": row["nome"]}


def atualizar_perfil(cursor: RealDictCursor, uid: str, dados: PerfilUpdateInput) -> None:
    """Actualiza nome e/ou email."""
    cursor.execute("SELECT id FROM utilizadores WHERE email=%s AND id != %s", (dados.email, uid))
    if cursor.fetchone():
        raise ErroDominio(400, "EMAIL_EM_USO", "Email já está em uso")

    cursor.execute("UPDATE utilizadores SET nome=%s, email=%s WHERE id=%s", (dados.nome, dados.email, uid))


def atualizar_password(cursor: RealDictCursor, uid: str, dados: PasswordUpdateInput) -> str:
    """Muda a password e invalida sessões anteriores. Devolve o email (para o router
    poder emitir um token novo já válido)."""
    cursor.execute("SELECT password, email FROM utilizadores WHERE id=%s", (uid,))
    row = cursor.fetchone()
    if not verificar_password(dados.password_atual, row["password"]):
        raise ErroDominio(401, "PASSWORD_INCORRETA", "Password atual incorreta")

    cursor.execute(
        "UPDATE utilizadores SET password=%s, sessoes_invalidadas_em = now() WHERE id=%s",
        (encriptar_password(dados.password_nova), uid)
    )
    return row["email"]


def terminar_todas_as_sessoes(cursor: RealDictCursor, uid: str) -> None:
    """Invalida todos os tokens emitidos até agora, incluindo o usado neste pedido."""
    cursor.execute("UPDATE utilizadores SET sessoes_invalidadas_em = now() WHERE id=%s", (uid,))


def eliminar_conta_utilizador(cursor: RealDictCursor, uid: str) -> None:
    """Elimina a conta e todos os dados associados — contas, categorias, movimentos,
    categorias_aprendidas e ajustes_saldo caem todos em ON DELETE CASCADE."""
    cursor.execute("DELETE FROM utilizadores WHERE id=%s", (uid,))
