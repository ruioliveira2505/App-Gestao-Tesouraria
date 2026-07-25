"""Utilitários pequenos partilhados entre serviços — nada aqui é lógica de negócio."""

from datetime import date


def fmt_data_pt(valor: str | date | None) -> str | None:
    """Formata uma data para "dd-mm-aaaa", para usar em mensagens de erro."""
    if valor is None:
        return valor
    if isinstance(valor, str):
        valor = date.fromisoformat(valor)
    return valor.strftime("%d-%m-%Y")


def lista_sql(coluna: str, valores_str: str | None) -> tuple[str, list[str]]:
    """Fragmento SQL "AND coluna IN (...)" a partir de uma lista CSV de valores — `coluna`
    é sempre um literal escolhido pelo código chamador, nunca vindo do pedido HTTP."""
    if not valores_str:
        return "", []
    valores = [v for v in valores_str.split(',') if v.strip()]
    if not valores:
        return "", []
    placeholders = ','.join(['%s'] * len(valores))
    return f"AND {coluna} IN ({placeholders})", valores
