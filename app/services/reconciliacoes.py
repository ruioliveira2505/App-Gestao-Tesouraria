def atualizar_saldo_atual(cursor, conta_id):
    cursor.execute("""
        SELECT saldo_real FROM ajustes_saldo WHERE conta_id=%s ORDER BY data DESC LIMIT 1
    """, (conta_id,))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE contas SET saldo=%s WHERE id=%s", (row[0], conta_id))


def primeiro_movimento_data(cursor, conta_id):
    cursor.execute("SELECT MIN(data) FROM movimentos WHERE conta_id=%s", (conta_id,))
    row = cursor.fetchone()
    return str(row[0]) if row and row[0] else None


def reconciliacao_mais_antiga_data(cursor, conta_id):
    cursor.execute("SELECT MIN(data) FROM ajustes_saldo WHERE conta_id=%s", (conta_id,))
    row = cursor.fetchone()
    return str(row[0]) if row and row[0] else None