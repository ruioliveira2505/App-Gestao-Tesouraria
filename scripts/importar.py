import json

from app.db.database import get_connection, release_connection
from app.services.categorizacao import categorizar


def importar_contas(cursor, contas):
    print("A inserir contas...")

    for conta in contas:
        cursor.execute(
            """
            INSERT INTO contas (
                id, nome, banco, iban, moeda, saldo, tipo, utilizador_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """,
            (
                conta["id"],
                conta["nome"],
                conta["banco"],
                conta["iban"],
                conta["moeda"],
                conta["saldo"],
                conta.get("tipo", "corrente"),
                1,
            ),
        )

        print(
            f"  {conta['nome']} — "
            f"{conta['banco']} — "
            f"{conta['iban']}"
        )

        # Apenas cria a reconciliação inicial quando a conta é inserida
        if cursor.rowcount == 1:
            cursor.execute(
                """
                INSERT INTO ajustes_saldo (
                    conta_id,
                    data,
                    saldo_real
                )
                VALUES (%s, %s, %s)
                ON CONFLICT (conta_id, data) DO NOTHING
                """,
                (
                    conta["id"],
                    "2026-04-30",
                    conta["saldo"],
                ),
            )


def importar_movimentos(cursor, conn, movimentos):
    print("\nA inserir movimentos...")

    for movimento in movimentos:
        categoria_id, origem = categorizar(
            movimento["descricao"],
            movimento["valor"],
            1,
            conn,
        )

        cursor.execute(
            """
            INSERT INTO movimentos (
                id,
                conta_id,
                data,
                descricao,
                valor,
                categoria_id,
                origem_cat,
                utilizador_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """,
            (
                movimento["id"],
                movimento["conta_id"],
                movimento["data"],
                movimento["descricao"],
                movimento["valor"],
                categoria_id,
                origem,
                1,
            ),
        )

        print(
            f"  {movimento['data']} | "
            f"{movimento['descricao']:<38} | "
            f"id={categoria_id} [{origem}]"
        )


def main():
    with open("scripts/dados_mock.json", "r", encoding="utf-8") as ficheiro:
        dados = json.load(ficheiro)

    conn = get_connection()

    try:
        cursor = conn.cursor()

        importar_contas(cursor, dados["contas"])
        importar_movimentos(cursor, conn, dados["movimentos"])

        conn.commit()
        cursor.close()

        print("\nImportação concluída.")

    finally:
        release_connection(conn)


if __name__ == "__main__":
    main()


# antes de implementar este script deve haver 1 user registado
# correr para importar os dados_mock para base de dados (user_id 1):
# python -m scripts.importat