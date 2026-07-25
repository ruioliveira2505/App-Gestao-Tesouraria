"""Infra-estrutura dos testes E2E (Playwright, browser a sério).

Ao contrário do resto da suite (que usa `TestClient` — chama a app em processo, sem rede
a sério), o Playwright controla um browser real, que faz pedidos HTTP a sério. Por isso
precisa de um servidor a sério à escuta — não dá para apontar a `TestClient`.

`tests/conftest.py` (o conftest pai) já trata de: apontar `DB_NAME` para
`tesouraria_test` antes de `app.main` ser importado, reconstruir o schema uma vez por
sessão, e limpar as tabelas antes de cada teste — tudo isso continua a aplicar-se aqui
também (fixtures autouse do conftest pai aplicam-se às subpastas).
"""

import socket
import threading
import time

import pytest
import uvicorn

from app.main import app


def pytest_collection_modifyitems(items):
    """Marca automaticamente todos os testes desta pasta como "e2e" — um `pytestmark` a
    este nível não chega (só se propaga dentro do próprio módulo do conftest, não aos
    ficheiros de teste vizinhos, confirmado ao testar). Dá para correr só estes com
    "pytest -m e2e", ou saltá-los com "pytest -m 'not e2e'" ao iterar rápido em código
    que não é frontend."""
    for item in items:
        if "tests/e2e/" in str(item.fspath).replace("\\", "/"):
            item.add_marker(pytest.mark.e2e)


def _porta_livre() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(autouse=True)
def falha_se_houver_erro_de_consola(page):
    """Apanha erros JS não tratados e console.error durante o teste — a rede de segurança
    contra o principal risco da migração para módulos ES: uma função só referenciada num
    onclick/onchange do HTML (ou uma variável global renomeada) que fica por importar/expor
    em window só rebenta quando alguém carrega nesse botão específico, e passa
    silenciosamente por qualquer teste que não exercite exactamente esse caminho."""
    erros = []

    def registar_console(msg):
        # "Failed to load resource" é o próprio browser a assinalar um pedido HTTP falhado
        # (401, ligação abortada, etc.) — ruído esperado nos testes que simulam essas
        # falhas de propósito (ver test_api_erros_e2e.py), não um erro de JS da app.
        if msg.type == "error" and "Failed to load resource" not in msg.text:
            erros.append(msg.text)

    page.on("pageerror", lambda exc: erros.append(str(exc)))
    page.on("console", registar_console)
    yield
    assert not erros, f"Erro(s) de consola/JS durante o teste: {erros}"


@pytest.fixture(scope="session")
def live_server():
    """Arranca app.main:app a sério, numa thread, contra a BD de teste. Session-scoped —
    um servidor só para todos os testes E2E (mais rápido; o isolamento entre testes já
    vem da limpeza de tabelas do conftest pai, não precisa de um servidor por teste)."""
    porta = _porta_livre()
    config = uvicorn.Config(app, host="127.0.0.1", port=porta, log_level="warning")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    while not server.started:
        time.sleep(0.05)

    yield f"http://127.0.0.1:{porta}"

    server.should_exit = True
    thread.join(timeout=5)
