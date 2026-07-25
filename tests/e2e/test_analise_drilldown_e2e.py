"""Cobertura nova para a página de Análise — trocar de aba, expandir/recolher categorias e
o drill-down (por grupo e por categoria). Nenhum destes onclick (muitos gerados dentro de
template literals JS, como o botão de drill-down em cada linha de grupo/categoria) tinha
teste algum antes da migração para módulos ES."""


def _registar_com_movimento(page, live_server, email):
    page.goto(f"{live_server}/static/index.html")
    page.click("text=Criar conta")
    page.fill("#reg-nome", "Lara E2E")
    page.fill("#reg-email", email)
    page.fill("#reg-password", "senha12345")
    page.click("#btn-registo")
    page.wait_for_selector("#app-screen", state="visible")

    page.click(".btn-fab[aria-label='Adicionar conta']")
    page.wait_for_selector("#modal-conta", state="visible")
    page.fill("#conta-nome", "Conta Análise E2E")
    page.click("#conta-moeda-wrapper")
    page.wait_for_selector("#conta-moeda-panel.aberto")
    page.click("#conta-moeda-panel >> text=EUR")
    page.fill("#conta-saldo", "1000")
    page.click("#btn-guardar-conta")
    page.wait_for_selector("#modal-conta", state="hidden")

    page.click('.friso-item[data-pagina="movimentos"]')
    page.wait_for_selector("#page-movimentos.active")
    page.click(".btn-fab[aria-label='Adicionar movimento']")
    page.wait_for_selector("#modal-movimento", state="visible")
    page.click("#mov-conta-wrapper")
    page.wait_for_selector("#mov-conta-panel.aberto")
    page.click("#mov-conta-panel >> text=Conta Análise E2E")
    page.click("#mov-tipo-wrapper")
    page.wait_for_selector("#mov-tipo-panel.aberto")
    page.click("#mov-tipo-panel >> text=Saída")
    page.click("#mov-categoria-wrapper")
    page.wait_for_selector("#mov-categoria-panel.aberto")
    page.click("#mov-categoria-panel >> text=Supermercado")
    page.fill("#mov-descricao", "Compras Análise E2E")
    page.fill("#mov-valor", "75")
    page.click("#btn-guardar-movimento")
    page.wait_for_selector("#modal-movimento", state="hidden")


def test_trocar_aba_e_expandir_recolher_categorias(page, live_server):
    _registar_com_movimento(page, live_server, "lara.analise@exemplo.com")
    page.click('.friso-item[data-pagina="analise"]')
    page.wait_for_selector("#page-analise.active")
    page.click("#btn-tipo-out")  # o movimento criado é uma saída; "Entradas" é o padrão
    page.wait_for_selector(".grupo-bar-row")

    page.click('.analise-tab[data-aba="recorrencias"]')
    page.wait_for_selector("#analise-secao-recorrencias.active")
    page.click('.analise-tab[data-aba="resumo"]')
    page.wait_for_selector("#analise-secao-resumo.active")

    # alternarExpandirTodos — expande/recolhe todos os sub-grupos de uma vez
    page.click("text=Categorias")
    page.wait_for_timeout(200)
    page.click("text=Categorias")


def test_drilldown_de_grupo_e_de_categoria(page, live_server):
    _registar_com_movimento(page, live_server, "lara.drilldown@exemplo.com")
    page.click('.friso-item[data-pagina="analise"]')
    page.wait_for_selector("#page-analise.active")
    page.click("#btn-tipo-out")  # o movimento criado é uma saída; "Entradas" é o padrão
    page.wait_for_selector(".grupo-bar-row")

    # drill-down por grupo
    page.click(".grupo-bar-row .btn-drilldown")
    page.wait_for_selector("#modal-drilldown", state="visible")
    page.wait_for_selector("#grafico-drilldown")
    page.click("#modal-drilldown >> button[aria-label='Fechar']")
    page.wait_for_selector("#modal-drilldown", state="hidden")

    # drill-down por categoria — dentro do sub-grupo, que é preciso expandir primeiro
    page.click(".grupo-bar-row .linha-topo")
    page.wait_for_selector(".sub-grupo .sub-item")
    page.click(".sub-item .btn-drilldown")
    page.wait_for_selector("#modal-drilldown", state="visible")
    page.wait_for_selector("#grafico-drilldown")
    page.click("#modal-drilldown >> button[aria-label='Fechar']")
    page.wait_for_selector("#modal-drilldown", state="hidden")
