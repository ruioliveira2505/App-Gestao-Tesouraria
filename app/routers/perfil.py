from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import utilizador_atual
from app.core.security import encriptar_password, verificar_password
from app.db.database import get_connection
from app.schemas.perfil import PasswordUpdateInput, PerfilUpdateInput

router = APIRouter()


@router.get("/me")
def perfil(utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT nome, email FROM utilizadores WHERE id=%s", (utilizador["sub"],))
        nome, email = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    return {"email": email, "id": utilizador["sub"], "nome": nome}


@router.put("/me")
def atualizar_perfil(dados: PerfilUpdateInput, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM utilizadores WHERE email=%s AND id != %s", (dados.email, utilizador["sub"]))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email já está em uso")

        cursor.execute("UPDATE utilizadores SET nome=%s, email=%s WHERE id=%s", (dados.nome, dados.email, utilizador["sub"]))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return {"ok": True, "nome": dados.nome}


@router.put("/me/password")
def atualizar_password(dados: PasswordUpdateInput, utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT password FROM utilizadores WHERE id=%s", (utilizador["sub"],))
        hash_atual = cursor.fetchone()[0]
        if not verificar_password(dados.password_atual, hash_atual):
            raise HTTPException(status_code=401, detail="Password atual incorreta")

        cursor.execute("UPDATE utilizadores SET password=%s WHERE id=%s", (encriptar_password(dados.password_nova), utilizador["sub"]))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return {"ok": True}


@router.delete("/me")
def eliminar_conta_utilizador(utilizador: dict = Depends(utilizador_atual)):
    conn = get_connection()
    cursor = conn.cursor()
    uid = utilizador["sub"]
    try:
        cursor.execute("DELETE FROM categorias_aprendidas WHERE utilizador_id=%s", (uid,))
        cursor.execute("DELETE FROM movimentos WHERE utilizador_id=%s", (uid,))
        cursor.execute("DELETE FROM categorias WHERE utilizador_id=%s", (uid,))
        cursor.execute("DELETE FROM contas WHERE utilizador_id=%s", (uid,))  # ajustes_saldo caem em CASCADE
        cursor.execute("DELETE FROM utilizadores WHERE id=%s", (uid,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return {"ok": True}