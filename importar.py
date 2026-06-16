import json
from database import get_connection
from nordigen import categorizar

# ── carregar dados mock ─────────────────────────────────────
with open("dados_mock.json", "r", encoding="utf-8") as f:
    dados = json.load(f)

conn = get_connection()
cursor = conn.cursor()

# ── inserir contas ──────────────────────────────────────────
print("A inserir contas...")

for conta in dados["contas"]:
    cursor.execute("""
        INSERT INTO contas (id, banco, iban, moeda, saldo)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """, (
        conta["id"],
        conta["banco"],
        conta["iban"],
        conta["moeda"],
        conta["saldo"],
    ))
    print(f"  {conta['banco']} — {conta['iban']}")

# ── inserir movimentos ──────────────────────────────────────
print("\nA inserir movimentos...")

for m in dados["movimentos"]:
    categoria, origem = categorizar(m["descricao"])

    cursor.execute("""
        INSERT INTO movimentos (id, conta_id, data, descricao, valor, categoria, origem_cat)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """, (
        m["id"],
        m["conta_id"],
        m["data"],
        m["descricao"],
        m["valor"],
        categoria,
        origem,
    ))
    print(f"  {m['data']} | {m['descricao']:<38} | {categoria}")

# ── confirmar e fechar ──────────────────────────────────────
conn.commit()
cursor.close()
conn.close()

print("\nImportação concluída.")