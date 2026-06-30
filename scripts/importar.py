import json
from app.db.database import get_connection, release_connection, release_connection
from app.services.categorizacao import categorizar

with open("scripts/dados_mock.json", "r", encoding="utf-8") as f:
    dados = json.load(f)

conn = get_connection()
cursor = conn.cursor()

print("A inserir contas...")
for conta in dados["contas"]:
    cursor.execute("""
        INSERT INTO contas (id, nome, banco, iban, moeda, saldo, tipo, utilizador_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """, (conta["id"], conta["nome"], conta["banco"], conta["iban"], conta["moeda"], conta["saldo"], conta.get("tipo", "corrente"), 1))
    print(f"  {conta['nome']} — {conta['banco']} — {conta['iban']}")
    
    if cursor.rowcount == 1:  # só insere reconciliação se a conta acabou de ser criada agora
        cursor.execute("""
            INSERT INTO ajustes_saldo (conta_id, data, saldo_real)
            VALUES (%s, %s, %s)
            ON CONFLICT (conta_id, data) DO NOTHING
        """, (conta["id"], "2026-04-30", conta["saldo"]))
    

print("\nA inserir movimentos...")
for m in dados["movimentos"]:
    categoria_id, origem = categorizar(m["descricao"], m["valor"], 1, conn)
    cursor.execute("""
        INSERT INTO movimentos (id, conta_id, data, descricao, valor, categoria_id, origem_cat, utilizador_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """, (m["id"], m["conta_id"], m["data"], m["descricao"], m["valor"], categoria_id, origem, 1))
    print(f"  {m['data']} | {m['descricao']:<38} | id={categoria_id} [{origem}]")

conn.commit()
cursor.close()
release_connection(conn)
print("\nImportação concluída.")