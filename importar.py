import json
from app.db.database import get_connection
from app.services.categorizacao import categorizar

with open("dados_mock.json", "r", encoding="utf-8") as f:
    dados = json.load(f)

conn = get_connection()
cursor = conn.cursor()

print("A inserir contas...")
for conta in dados["contas"]:
    cursor.execute("""
        INSERT INTO contas (id, banco, iban, moeda, saldo, utilizador_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """, (conta["id"], conta["banco"], conta["iban"], conta["moeda"], conta["saldo"], 1))
    print(f"  {conta['banco']} — {conta['iban']}")

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
conn.close()
print("\nImportação concluída.")