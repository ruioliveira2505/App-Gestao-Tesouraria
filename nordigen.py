import json

# ── carregar dados ──────────────────────────────────────────
with open("dados_mock.json", "r", encoding="utf-8") as f:
    dados = json.load(f)

movimentos = dados["movimentos"]

# ── carregar cache (se existir) ─────────────────────────────
try:
    with open("cache.json", "r", encoding="utf-8") as f:
        cache = json.load(f)
except FileNotFoundError:
    cache = {}

# ── regras de categorização ─────────────────────────────────
REGRAS = [
    ("salario",       "salários"),
    ("edp",           "utilities"),
    ("nos ",          "utilities"),
    ("galp",          "utilities"),
    ("continente",    "supermercado"),
    ("pingo doce",    "supermercado"),
    ("aldi",          "supermercado"),
    ("mb way",        "transferências"),
    ("transferencia", "transferências"),
    ("at ",           "impostos"),
    ("pagamento iva", "impostos"),
    ("pagamento irs", "impostos"),
]

def categorizar_por_regras(descricao):
    descricao_lower = descricao.lower()
    for palavra, categoria in REGRAS:
        if palavra in descricao_lower:
            return categoria
    return None  # sem resultado

def categorizar(descricao):
    # camada 1 — regras
    categoria = categorizar_por_regras(descricao)
    if categoria:
        return categoria, "regra"

    # camada 2 — cache
    if descricao in cache:
        return cache[descricao], "cache"

    # não encontrou nada
    return "por categorizar", "sem_match"

# ── aplicar e mostrar ───────────────────────────────────────
print(f"{'DATA':<12} {'DESCRIÇÃO':<38} {'VALOR':>10}  {'CATEGORIA':<18} ORIGEM")
print("-" * 90)

for m in movimentos:
    categoria, origem = categorizar(m["descricao"])
    m["categoria"] = categoria
    print(f"{m['data']:<12} {m['descricao']:<38} {m['valor']:>10.2f}  {categoria:<18} [{origem}]")

# ── guardar cache atualizada ────────────────────────────────
with open("cache.json", "w", encoding="utf-8") as f:
    json.dump(cache, f, ensure_ascii=False, indent=2)

print("\nCache guardada.")


# ── resumo por categoria ────────────────────────────────────
resumo = {}

for m in movimentos:
    cat = m["categoria"]
    valor = m["valor"]

    if cat not in resumo:
        resumo[cat] = {"entradas": 0.0, "saidas": 0.0, "n": 0}

    if valor > 0:
        resumo[cat]["entradas"] += valor
    else:
        resumo[cat]["saidas"] += valor

    resumo[cat]["n"] += 1

print("\n── resumo por categoria ────────────────────────────")
print(f"{'CATEGORIA':<20} {'ENTRADAS':>10}  {'SAÍDAS':>10}  {'Nº':>4}")
print("-" * 52)

for cat, valores in resumo.items():
    print(
        f"{cat:<20} "
        f"{valores['entradas']:>10.2f}  "
        f"{valores['saidas']:>10.2f}  "
        f"{valores['n']:>4}"
    )

total_entradas = sum(v["entradas"] for v in resumo.values())
total_saidas   = sum(v["saidas"]   for v in resumo.values())

print("-" * 52)
print(f"{'TOTAL':<20} {total_entradas:>10.2f}  {total_saidas:>10.2f}")
print(f"\nSaldo líquido do período: {total_entradas + total_saidas:.2f} EUR")