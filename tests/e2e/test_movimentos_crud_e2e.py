"""Cobertura nova para o CRUD de movimentos através do formulário real (não apenas a
pesquisa, já coberta por test_movimentos_e2e.py) — os seletores de conta/tipo/categoria do
formulário e o menu de acções da linha da tabela não tinham teste algum antes da migração
para módulos ES."""


def _registar(page, live_server, email):
    page.goto(f"{live_server}/static/index.html")
    page.click("text=Criar conta")
    page.fill("#reg-nome", "Karin E2E")
    page.fill("#reg-email", email)
    page.fill("#reg-password", "senha12345")
    page.click("#btn-registo")
    page.wait_for_selector("#app-screen", state="visible")


def _criar_conta(page, nome="Conta Movimentos E2E"):
    page.click(".btn-fab[aria-label='Adicionar conta']")
    page.wait_for_selector("#modal-conta", state="visible")
    page.fill("#conta-nome", nome)
    page.click("#conta-moeda-wrapper")
    page.wait_for_selector("#conta-moeda-panel.aberto")
    page.click("#conta-moeda-panel >> text=EUR")
    page.fill("#conta-saldo", "1000")
    page.click("#btn-guardar-conta")
    page.wait_for_selector("#modal-conta", state="hidden")


def _clicar_menu_acoes(page, linha):
    # ver nota em test_reconciliacoes_e2e.py — <main> fecha o menu ao fazer scroll, e o
    # auto-scroll do Playwright antes do clique dispara-o se não se garantir isto primeiro.
    botao = linha.locator("button[aria-label='Mais ações']")
    botao.scroll_into_view_if_needed()
    page.wait_for_timeout(200)
    botao.click()


def test_criar_editar_e_eliminar_movimento(page, live_server):
    _registar(page, live_server, "karin.movimentos@exemplo.com")
    page.wait_for_selector("#page-contas.active")
    _criar_conta(page)

    page.click('.friso-item[data-pagina="movimentos"]')
    page.wait_for_selector("#page-movimentos.active")

    # criar — via formulário completo, incluindo os três seletores personalizados
    page.click(".btn-fab[aria-label='Adicionar movimento']")
    page.wait_for_selector("#modal-movimento", state="visible")

    page.click("#mov-conta-wrapper")
    page.wait_for_selector("#mov-conta-panel.aberto")
    page.click("#mov-conta-panel >> text=Conta Movimentos E2E")

    page.click("#mov-tipo-wrapper")
    page.wait_for_selector("#mov-tipo-panel.aberto")
    page.click("#mov-tipo-panel >> text=Saída")

    page.click("#mov-categoria-wrapper")
    page.wait_for_selector("#mov-categoria-panel.aberto")
    page.click("#mov-categoria-panel >> text=Supermercado")

    page.fill("#mov-descricao", "Compras E2E")
    page.fill("#mov-valor", "42.5")
    page.click("#btn-guardar-movimento")
    page.wait_for_selector("#modal-movimento", state="hidden")

    linha = page.locator("#tabela-movimentos tr", has_text="Compras E2E")
    linha.wait_for()
    assert "42,50" in linha.inner_text()

    # editar — via menu de acções (abrirEditarMovimento)
    _clicar_menu_acoes(page, linha.first)
    page.click("#menu-acoes-flutuante >> text=Editar")
    page.wait_for_selector("#modal-movimento", state="visible")
    page.fill("#mov-descricao", "Compras E2E Editado")
    page.click("#btn-guardar-movimento")
    page.wait_for_selector("#modal-movimento", state="hidden")
    page.locator("#tabela-movimentos tr", has_text="Compras E2E Editado").wait_for()

    # eliminar
    linha = page.locator("#tabela-movimentos tr", has_text="Compras E2E Editado")
    _clicar_menu_acoes(page, linha.first)
    page.click("#menu-acoes-flutuante >> text=Eliminar")
    page.wait_for_selector("#confirm-modal.open")
    page.click("#confirm-modal-btn-confirmar")
    page.wait_for_selector("#tabela-movimentos >> text=Ainda não tens movimentos")
