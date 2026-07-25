"""Ferramenta de desenvolvimento — NÃO é um importador de extractos bancários a sério.

Semeia `scripts/dados_mock.json` (dados inventados) para o utilizador id=1, passando cada
movimento pelo pipeline real de categorização (cache → LLM → fallback) só para ter dados
de teste com categorias já atribuídas, parecidos com o que aconteceria com uma importação
real. Não há nenhum endpoint HTTP equivalente — a app não tem hoje uma funcionalidade de
importação de extractos (ver analise-tesouraria-historico.md, secção "Higiene do repositório").
"""

import json
from datetime import date, timedelta
from pathlib import Path

from psycopg2.extensions import connection as PgConnection
from psycopg2.extensions import cursor as PgCursor

from app.db.database import get_connection, release_connection
from app.services.categorizacao import categorizar

PASTA_RAIZ = Path(__file__).resolve().parent.parent


def importar_contas(cursor: PgCursor, contas: list[dict], movimentos: list[dict]) -> None:
    print("A inserir contas...")

    # data mais antiga de movimentos, por conta, para calcular a âncora (data_ancora fica
    # sempre um dia antes do movimento mais antigo dessa conta)
    data_mais_antiga_por_conta = {}
    for m in movimentos:
        conta_id = m["conta_id"]
        if conta_id not in data_mais_antiga_por_conta or m["data"] < data_mais_antiga_por_conta[conta_id]:
            data_mais_antiga_por_conta[conta_id] = m["data"]

    for conta in contas:
        primeiro_movimento = data_mais_antiga_por_conta.get(conta["id"])
        if primeiro_movimento:
            ano, mes, dia = map(int, primeiro_movimento.split("-"))
            data_ancora = (date(ano, mes, dia) - timedelta(days=1)).isoformat()
        else:
            data_ancora = date.today().isoformat()

        # data_ancora/saldo_ancora são a âncora da conta — atributo próprio de `contas`
        # desde a migração 0013, não uma linha em `ajustes_saldo` (ver ARCHITECTURE.md).
        cursor.execute(
            """
            INSERT INTO contas (
                id, nome, banco, iban, moeda, tipo, utilizador_id, data_ancora, saldo_ancora
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """,
            (
                conta["id"],
                conta["nome"],
                conta["banco"],
                conta["iban"],
                conta["moeda"],
                conta.get("tipo", "corrente"),
                1,
                data_ancora,
                conta["saldo"],
            ),
        )

        print(
            f"  {conta['nome']} — "
            f"{conta['banco']} — "
            f"{conta['iban']}"
        )
        if cursor.rowcount == 1:
            print(f"    → âncora em {data_ancora}")


def importar_movimentos(cursor: PgCursor, conn: PgConnection, movimentos: list[dict]) -> None:
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


def main() -> None:
    with open(PASTA_RAIZ / "scripts" / "dados_mock.json", encoding="utf-8") as ficheiro:
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


# antes de correr este script deve haver 1 user registado
# correr para semear os dados_mock na base de dados de desenvolvimento (user_id 1):
# python -m scripts.seed_dev
