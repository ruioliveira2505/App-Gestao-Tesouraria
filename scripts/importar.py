import json
from datetime import date, timedelta

from app.db.database import get_connection, release_connection
from app.services.categorizacao import categorizar


def importar_contas(cursor, contas, movimentos):
    print("A inserir contas...")

    # data mais antiga de movimentos, por conta, para calcular a reconciliação inicial
    data_mais_antiga_por_conta = {}
    for m in movimentos:
        conta_id = m["conta_id"]
        if conta_id not in data_mais_antiga_por_conta or m["data"] < data_mais_antiga_por_conta[conta_id]:
            data_mais_antiga_por_conta[conta_id] = m["data"]

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

        # A reconciliação inicial fica um dia antes do movimento mais antigo desta conta
        # (se não houver movimentos para esta conta, usa-se hoje como fallback)
        primeiro_movimento = data_mais_antiga_por_conta.get(conta["id"])
        if primeiro_movimento:
            ano, mes, dia = map(int, primeiro_movimento.split("-"))
            data_reconciliacao = (date(ano, mes, dia) - timedelta(days=1)).isoformat()
        else:
            data_reconciliacao = date.today().isoformat()

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
                    data_reconciliacao,
                    conta["saldo"],
                ),
            )
            print(f"    → reconciliação inicial em {data_reconciliacao}")


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

        importar_contas(cursor, dados["contas"], dados["movimentos"])
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
# python -m scripts.importar