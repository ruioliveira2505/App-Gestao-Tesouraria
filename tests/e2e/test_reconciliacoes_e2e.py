"""Cobertura nova para reconciliações de saldo — zona sem teste algum antes da migração
para módulos ES. O menu de acções da conta (toggleMenuAcoesConta) e o próprio formulário de
reconciliação (mostrarFormReconciliacao/guardarReconciliacao/eliminarReconciliacao) só
existem como onclick gerados dinamicamente dentro de template literals JS."""


def _registar(page, live_server, email):
    page.goto(f"{live_server}/static/index.html")
    page.click("text=Criar conta")
    page.fill("#reg-nome", "Joana E2E")
    page.fill("#reg-email", email)
    page.fill("#reg-password", "senha12345")
    page.click("#btn-registo")
    page.wait_for_selector("#app-screen", state="visible")


def _criar_conta(page, nome="Conta Reconciliação E2E"):
    page.click(".btn-fab[aria-label='Adicionar conta']")
    page.wait_for_selector("#modal-conta", state="visible")
    page.fill("#conta-nome", nome)
    page.click("#conta-moeda-wrapper")
    page.wait_for_selector("#conta-moeda-panel.aberto")
    page.click("#conta-moeda-panel >> text=EUR")
    page.fill("#conta-saldo", "1000")
    page.click("#btn-guardar-conta")
    page.wait_for_selector("#modal-conta", state="hidden")
    page.locator(".linha-conta, tr", has_text=nome).first.wait_for()


def _clicar_menu_acoes(page, linha):
    # scroll explícito antes do clique: <main> fecha o menu de acções ao fazer scroll (de
    # propósito, para não ficar "pendurado" se o conteúdo por baixo se mexer) — sem isto, o
    # auto-scroll que o Playwright faz para o botão ficar visível dispara esse scroll DEPOIS
    # do clique ter aberto o menu, fechando-o de imediato.
    botao = linha.locator("button[aria-label='Mais ações']")
    botao.scroll_into_view_if_needed()
    page.wait_for_timeout(200)
    botao.click()


def _abrir_reconciliacoes(page, nome_conta):
    linha = page.locator("tr", has_text=nome_conta).first
    _clicar_menu_acoes(page, linha)
    page.click("#menu-acoes-flutuante >> text=Reconciliações")
    page.wait_for_selector("#modal-reconciliacoes", state="visible")


def test_criar_editar_e_eliminar_reconciliacao(page, live_server):
    _registar(page, live_server, "joana.reconc@exemplo.com")
    page.wait_for_selector("#page-contas.active")
    _criar_conta(page)
    _abrir_reconciliacoes(page, "Conta Reconciliação E2E")

    # criar reconciliação — a data já vem pré-preenchida com hoje
    page.click("#btn-add-reconciliacao")
    page.wait_for_selector("#form-reconciliacao", state="visible")
    page.fill("#reconc-valor", "950")
    page.click("#btn-guardar-reconciliacao")
    page.wait_for_selector("#form-reconciliacao", state="hidden")
    page.locator("#tabela-reconciliacoes tr", has_text="950").wait_for()

    # editar — via menu de acções (toggleMenuAcoesReconciliacao)
    linha = page.locator("#tabela-reconciliacoes tr", has_text="950").first
    _clicar_menu_acoes(page, linha)
    page.click("#menu-acoes-flutuante >> text=Editar")
    page.wait_for_selector("#form-reconciliacao", state="visible")
    page.fill("#reconc-valor", "900")
    page.click("#btn-guardar-reconciliacao")
    page.wait_for_selector("#form-reconciliacao", state="hidden")
    page.locator("#tabela-reconciliacoes tr", has_text="900").wait_for()
    assert page.locator("#tabela-reconciliacoes tr", has_text="950").count() == 0

    # eliminar
    linha = page.locator("#tabela-reconciliacoes tr", has_text="900").first
    _clicar_menu_acoes(page, linha)
    page.click("#menu-acoes-flutuante >> text=Eliminar")
    page.wait_for_selector("#confirm-modal.open")
    page.click("#confirm-modal-btn-confirmar")
    page.wait_for_selector("#confirm-modal", state="hidden")
    # eliminarReconciliacao só chama a API depois da Promise do confirmarAcao resolver —
    # dá-se tempo ao pedido assíncrono antes de verificar o resultado
    page.wait_for_selector("#tabela-reconciliacoes >> text=Nenhuma correção realizada")
