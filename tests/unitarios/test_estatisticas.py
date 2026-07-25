"""Testes unitários da lógica pura de estatisticas.py — sem BD, sem TestClient, sem
fixtures de sessão. Ao contrário do resto da suite (tudo passa pela stack toda), estes
correm em milissegundos e testam só a função de cálculo, isolada (ver
app/services/estatisticas.py::_calcular_padrao_recorrente)."""

from datetime import date

from app.services.estatisticas import _calcular_padrao_recorrente


def test_menos_de_duas_ocorrencias_devolve_none():
    assert _calcular_padrao_recorrente([(date(2026, 1, 1), -10.0)]) is None
    assert _calcular_padrao_recorrente([]) is None


def test_ocorrencias_todas_na_mesma_data_devolve_none():
    """intervalo_medio == 0 — não dá para estimar uma próxima data nem regularidade."""
    mesma_data = date(2026, 1, 1)
    assert _calcular_padrao_recorrente([(mesma_data, -10.0), (mesma_data, -10.0)]) is None


def test_padrao_perfeitamente_regular():
    ocorrencias = [
        (date(2026, 1, 1), -17.99),
        (date(2026, 1, 31), -17.99),
        (date(2026, 3, 2), -17.99),  # 30 dias depois
    ]
    padrao = _calcular_padrao_recorrente(ocorrencias)
    assert padrao["ocorrencias"] == 3
    assert padrao["regular"] is True
    assert padrao["valor_medio"] == -17.99
    assert padrao["intervalo_medio_dias"] == 30
    assert padrao["ultima_vez"] == "2026-03-02"
    assert padrao["proxima_data_estimada"] == "2026-04-01"


def test_padrao_irregular():
    """Intervalos muito díspares (5 e 95 dias) — desvio-padrão bem acima de 40% da média."""
    ocorrencias = [
        (date(2026, 1, 1), -650.0),
        (date(2026, 1, 6), -650.0),
        (date(2026, 4, 11), -650.0),
    ]
    padrao = _calcular_padrao_recorrente(ocorrencias)
    assert padrao["regular"] is False


def test_valor_medio_arredondado_a_duas_casas():
    ocorrencias = [
        (date(2026, 1, 1), -10.0),
        (date(2026, 1, 15), -11.0),
        (date(2026, 1, 29), -10.5),
    ]
    padrao = _calcular_padrao_recorrente(ocorrencias)
    assert padrao["valor_medio"] == round((-10.0 - 11.0 - 10.5) / 3, 2)


def test_limite_exacto_de_40_por_cento_conta_como_regular():
    """regular = desvio/media < 0.4 (estrito) — construído para ficar mesmo abaixo."""
    ocorrencias = [
        (date(2026, 1, 1), -20.0),
        (date(2026, 1, 31), -20.0),   # intervalo 30
        (date(2026, 3, 1), -20.0),    # intervalo 29 — quase igual, desvio pequeno
    ]
    padrao = _calcular_padrao_recorrente(ocorrencias)
    assert padrao["regular"] is True
