"""Cobertura da primeira fatia vertical do i18n (PT/EN) — infra-estrutura (t()/
aplicarTraducoes()/mudarLingua) mais a página de Contas, a cobertura actual (ver
static/js/i18n.js). Frontend só — o backend continua sempre a devolver mensagens em
português; a tradução de erros fica ao critério de quem os mostra."""


def _registar(page, live_server, email):
    page.goto(f"{live_server}/static/index.html")
    page.click("text=Criar conta")
    page.fill("#reg-nome", "Íris i18n")
    page.fill("#reg-email", email)
    page.fill("#reg-password", "senha12345")
    page.click("#btn-registo")
    page.wait_for_selector("#app-screen", state="visible")


def _mudar_lingua(page, lingua):
    page.click("#avatar-wrapper")
    page.click(".avatar-menu-item[onclick=\"abrirModalConfiguracoes()\"]")
    page.wait_for_selector("#modal-configuracoes.open")
    page.click('.perfil-sidebar-item[data-secao="preferencias"]')
    page.click(f"#lingua-{lingua}")
    page.wait_for_timeout(150)
    page.click(".btn-fechar-modal-config")


def test_trocar_para_ingles_traduz_navegacao_e_pagina_contas(page, live_server):
    _registar(page, live_server, "iris.i18n.contas@exemplo.com")
    assert page.locator('.friso-item[data-pagina="contas"] .label').inner_text() == "Contas"
    assert page.locator("#page-contas h1").inner_text() == "Contas"

    _mudar_lingua(page, "en")

    assert page.locator('.friso-item[data-pagina="contas"] .label').inner_text() == "Accounts"
    assert page.locator('.friso-item[data-pagina="movimentos"] .label').inner_text() == "Transactions"
    assert page.locator('.friso-item[data-pagina="analise"] .label').inner_text() == "Analysis"
    assert page.locator("#page-contas h1").inner_text() == "Accounts"
    assert page.locator("#cabecalho-contas th").first.inner_text().strip().upper().startswith("NAME")
    assert page.locator(".btn-fab[aria-label='Add account']").count() == 1

    page.click(".btn-fab[aria-label='Add account']")
    page.wait_for_selector("#modal-conta", state="visible")
    assert page.locator("#modal-conta-titulo").inner_text() == "Add account"
    assert page.locator("#btn-guardar-conta").inner_text() == "Save"
    assert page.locator("#modal-conta .modal-footer .btn-secondary").inner_text() == "Cancel"
    page.click("#modal-conta .modal-footer .btn-secondary")


def test_trocar_lingua_persiste_e_volta_a_portugues(page, live_server):
    _registar(page, live_server, "iris.i18n.persistencia@exemplo.com")
    _mudar_lingua(page, "en")
    assert page.locator('.friso-item[data-pagina="contas"] .label').inner_text() == "Accounts"

    # persiste em localStorage, tal como o tema — sobrevive a um reload da página
    page.reload()
    page.wait_for_selector("#app-screen", state="visible")
    assert page.locator('.friso-item[data-pagina="contas"] .label').inner_text() == "Accounts"

    _mudar_lingua(page, "pt")
    assert page.locator('.friso-item[data-pagina="contas"] .label').inner_text() == "Contas"


def test_mensagens_de_erro_traduzem_por_codigo_com_fallback_para_portugues(page, live_server):
    """code é estável e sem língua (contrato já existente) — traduzirErro() só traduz se
    já houver entrada em ERROS_TRADUCOES; sem isso cai sempre no message (PT) do backend,
    nunca mostra uma chave em bruto ou "undefined"."""
    _registar(page, live_server, "iris.i18n.erros@exemplo.com")

    resultado = page.evaluate("""
        async () => {
            const utils = await import('/static/js/utils.js')
            const estado = await import('/static/js/estado.js')
            estado.estadoGlobal.lingua = 'en'
            return {
                com_ctx: utils.mensagemDeErro({detail: {code: 'STRING_TOO_SHORT', message: 'Tem de ter pelo menos 8 caracteres.', ctx: {min_length: 8}}}),
                sem_ctx: utils.mensagemDeErro({detail: {code: 'CONTA_NAO_ENCONTRADA', message: 'Conta não encontrada'}}),
                desconhecido: utils.mensagemDeErro({detail: {code: 'CODIGO_QUE_NAO_EXISTE_AINDA', message: 'Mensagem qualquer em português.'}}),
            }
        }
    """)
    assert resultado["com_ctx"] == "Must be at least 8 characters."
    assert resultado["sem_ctx"] == "Account not found"
    assert resultado["desconhecido"] == "Mensagem qualquer em português."


def test_pagina_movimentos_traduz_incluindo_nomes_de_categorias(page, live_server):
    """As categorias por omissão (com slug) têm de traduzir mesmo dentro de conteúdo
    gerado dinamicamente (seletor do formulário e linhas da tabela) — não só o texto
    estático da página, ver static/js/i18n.js::nomeCategoria."""
    _registar(page, live_server, "iris.i18n.movimentos@exemplo.com")

    page.click(".btn-fab[aria-label='Adicionar conta']")
    page.wait_for_selector("#modal-conta", state="visible")
    page.fill("#conta-nome", "Conta Movs i18n")
    page.click("#conta-moeda-wrapper")
    page.wait_for_selector("#conta-moeda-panel.aberto")
    page.click("#conta-moeda-panel >> text=EUR")
    page.fill("#conta-saldo", "500")
    page.click("#btn-guardar-conta")
    page.wait_for_selector("#modal-conta", state="hidden")

    _mudar_lingua(page, "en")

    page.click('.friso-item[data-pagina="movimentos"]')
    page.wait_for_selector("#page-movimentos.active")
    assert page.locator("#page-movimentos h1").inner_text() == "Transactions"

    page.click(".btn-fab[aria-label='Add transaction']")
    page.wait_for_selector("#modal-movimento", state="visible")
    assert page.locator("#modal-movimento-titulo").inner_text() == "Add transaction"

    page.click("#mov-conta-wrapper")
    page.wait_for_selector("#mov-conta-panel.aberto")
    page.click("#mov-conta-panel >> text=Conta Movs i18n")
    page.click("#mov-tipo-wrapper")
    page.wait_for_selector("#mov-tipo-panel.aberto")
    assert set(page.locator("#mov-tipo-lista .filtro-item-linha").all_inner_texts()) == {"Income", "Expense"}
    page.click("#mov-tipo-panel >> text=Expense")

    page.click("#mov-categoria-wrapper")
    page.wait_for_selector("#mov-categoria-panel.aberto")
    assert page.locator("#mov-categoria-panel >> text=Food").count() == 1
    assert page.locator("#mov-categoria-panel >> text=Supermarket").count() == 1
    page.click("#mov-categoria-panel >> text=Supermarket")

    page.fill("#mov-descricao", "Groceries i18n")
    page.fill("#mov-valor", "50")
    page.click("#btn-guardar-movimento")
    page.wait_for_selector("#modal-movimento", state="hidden")

    linha = page.locator("#tabela-movimentos tr", has_text="Groceries i18n")
    linha.wait_for()
    assert "Supermarket" in linha.inner_text()
    assert "Food" in linha.inner_text()


def _registar_com_movimento_analise(page, live_server, email):
    page.goto(f"{live_server}/static/index.html")
    page.click("text=Criar conta")
    page.fill("#reg-nome", "Íris i18n")
    page.fill("#reg-email", email)
    page.fill("#reg-password", "senha12345")
    page.click("#btn-registo")
    page.wait_for_selector("#app-screen", state="visible")

    page.click(".btn-fab[aria-label='Adicionar conta']")
    page.wait_for_selector("#modal-conta", state="visible")
    page.fill("#conta-nome", "Conta Analise i18n")
    page.click("#conta-moeda-wrapper")
    page.wait_for_selector("#conta-moeda-panel.aberto")
    page.click("#conta-moeda-panel >> text=EUR")
    page.fill("#conta-saldo", "1000")
    page.click("#btn-guardar-conta")
    page.wait_for_selector("#modal-conta", state="hidden")

    _mudar_lingua(page, "en")

    page.click('.friso-item[data-pagina="movimentos"]')
    page.wait_for_selector("#page-movimentos.active")
    page.click(".btn-fab[aria-label='Add transaction']")
    page.wait_for_selector("#modal-movimento", state="visible")
    page.click("#mov-conta-wrapper")
    page.wait_for_selector("#mov-conta-panel.aberto")
    page.click("#mov-conta-panel >> text=Conta Analise i18n")
    page.click("#mov-tipo-wrapper")
    page.wait_for_selector("#mov-tipo-panel.aberto")
    page.click("#mov-tipo-panel >> text=Expense")
    page.click("#mov-categoria-wrapper")
    page.wait_for_selector("#mov-categoria-panel.aberto")
    page.click("#mov-categoria-panel >> text=Supermarket")
    page.fill("#mov-descricao", "Groceries analise i18n")
    page.fill("#mov-valor", "75")
    page.click("#btn-guardar-movimento")
    page.wait_for_selector("#modal-movimento", state="hidden")


def test_pagina_analise_traduz_incluindo_nomes_de_categorias(page, live_server):
    """Os nomes de grupo/categoria em Análise vêm de /stats/grupos e /stats/mensal-detalhe
    — endpoints estendidos com grupo_slug/categoria_slug (à semelhança de /movimentos) para
    que nomeCategoria() também traduza aqui: nas barras, no drill-down e no texto estático."""
    _registar_com_movimento_analise(page, live_server, "iris.i18n.analise@exemplo.com")

    page.click('.friso-item[data-pagina="analise"]')
    page.wait_for_selector("#page-analise.active")
    assert page.locator("#page-analise h1").inner_text() == "Analysis"
    assert page.locator('.analise-tab[data-aba="resumo"]').inner_text() == "Summary"
    assert page.locator('.analise-tab[data-aba="recorrencias"]').inner_text() == "Recurring Expenses"

    page.click("#btn-tipo-out")  # o movimento criado é uma saída; "Entradas"/"Income" é o padrão
    page.wait_for_selector(".grupo-bar-row")
    assert page.locator(".grupo-bar-row .nome").first.inner_text() == "Food"
    page.click(".grupo-bar-row .linha-topo")
    page.wait_for_selector(".sub-grupo .sub-item")
    assert "Supermarket" in page.locator(".sub-item").first.inner_text()

    page.click(".grupo-bar-row .btn-drilldown")
    page.wait_for_selector("#modal-drilldown", state="visible")
    assert page.locator("#drawer-titulo").inner_text() == "Food"
    # .drilldown-titulo-label tem text-transform: uppercase em CSS — inner_text() reflete o
    # texto tal como é apresentado (maiúsculas), não o conteúdo em bruto do DOM.
    assert page.locator("#drawer-subtitulo").inner_text() == "MONTHLY TREND"
    page.click("#modal-drilldown >> button[aria-label='Close']")
    page.wait_for_selector("#modal-drilldown", state="hidden")


def test_meses_e_dias_traduzem_em_graficos_e_calendario(page, live_server):
    """fmtMes/fmtDiaCurto/fmtDiaCompleto (legendas dos gráficos de Análise e do gráfico de
    evolução de saldo em Contas) e o calendário próprio (nomes de mês completos no seletor,
    dias da semana abreviados no cabeçalho) tinham arrays de meses fixos em português,
    nunca verificados por nenhum teste — só apanhado ao reportar visualmente que "o gráfico
    de evolução de saldo ainda aparece em português"."""
    _registar(page, live_server, "iris.i18n.calendario@exemplo.com")
    _mudar_lingua(page, "en")

    # o painel de "Ordenar" (Contas/Movimentos/Análise-Recorrentes) também tinha os
    # rótulos de campo/direcção fixos em português, independentemente da língua
    assert page.locator("#ct-ordenar-btn-texto").inner_text() == "Sort: Name"

    resultado = page.evaluate("""
        async () => {
            const utils = await import('/static/js/utils.js')
            const i18n = await import('/static/js/i18n.js')
            return {
                fmtMes: utils.fmtMes('2026-02'),
                fmtDiaCurto: utils.fmtDiaCurto('2026-02-05'),
                fmtDiaCompleto: utils.fmtDiaCompleto('2026-02-05'),
                mesesCompletos: i18n.nomesMesesCompletos(),
                diasAbrev: i18n.nomesDiasAbrev(),
            }
        }
    """)
    assert resultado["fmtMes"] == "Feb 26"
    assert resultado["fmtDiaCurto"] == "05 Feb"
    assert resultado["fmtDiaCompleto"] == "05 Feb 2026"
    assert resultado["mesesCompletos"][1] == "February"
    assert resultado["diasAbrev"] == ["M", "T", "W", "T", "F", "S", "S"]

    # o calendário próprio (usado em Contas/Movimentos/Análise) mostra o mesmo em ecrã
    page.click('.friso-item[data-pagina="movimentos"]')
    page.wait_for_selector("#page-movimentos.active")
    page.click("#mov-periodo-wrapper")
    page.wait_for_selector('#calendario-range-panel[style*="display: flex"]')
    mes_select = page.locator("#calendario-range-panel select").nth(0)
    assert mes_select.locator("option").nth(1).inner_text() == "February"
    assert "This month" in page.locator("#calendario-range-panel").inner_text()
    assert page.locator("#calendario-range-panel .cal-nav").first.get_attribute("aria-label") == "Previous month"


def test_renomear_categoria_por_omissao_deixa_de_traduzir_automaticamente(page, live_server):
    """nomeCategoria() só traduz uma categoria por omissão enquanto o nome continuar igual
    ao de fábrica (CATEGORIAS_TRADUCOES.pt em i18n.js). Questão levantada pelo utilizador:
    se ele renomear "Supermercado" para algo sem relação nenhuma (ex. "Coisas Aleatórias"),
    mostrar "Supermarket" em inglês deixa de fazer sentido — a partir do rename, mostra-se
    sempre o texto tal como o utilizador o escreveu, nas duas línguas. Uma categoria irmã,
    não tocada, continua a traduzir normalmente (a mudança é só para a categoria editada)."""
    _registar(page, live_server, "iris.i18n.rename@exemplo.com")

    page.click("#avatar-wrapper")
    page.click(".avatar-menu-item[onclick=\"abrirModalConfiguracoes()\"]")
    page.wait_for_selector("#modal-configuracoes.open")
    page.click('.perfil-sidebar-item[data-secao="categorias"]')
    page.wait_for_selector("#lista-categorias-gestao .grupo-gestao")
    page.click("#cat-tipo-out")   # "Supermercado" é uma categoria de Saídas — "Entradas" é o separador por omissão

    categoria = page.locator(".categoria-gestao-item", has_text="Supermercado")
    categoria.scroll_into_view_if_needed()
    page.wait_for_timeout(200)
    categoria.locator("button", has_text="⋮").click()
    page.click("#menu-acoes-flutuante >> text=Editar")
    page.wait_for_selector("#modal-categoria-gestao", state="visible")
    page.fill("#categoria-gestao-nome", "Coisas Aleatórias")
    page.click("#btn-guardar-categoria-gestao")
    page.wait_for_selector("#modal-categoria-gestao", state="hidden")
    page.locator(".categoria-gestao-item", has_text="Coisas Aleatórias").wait_for()
    page.click(".btn-fechar-modal-config")

    _mudar_lingua(page, "en")

    page.click('.friso-item[data-pagina="movimentos"]')
    page.wait_for_selector("#page-movimentos.active")
    page.click(".btn-fab[aria-label='Add transaction']")
    page.wait_for_selector("#modal-movimento", state="visible")
    page.click("#mov-tipo-wrapper")
    page.wait_for_selector("#mov-tipo-panel.aberto")
    page.click("#mov-tipo-panel >> text=Expense")
    page.click("#mov-categoria-wrapper")
    page.wait_for_selector("#mov-categoria-panel.aberto")

    assert page.locator("#mov-categoria-panel >> text=Coisas Aleatórias").count() == 1
    assert page.locator("#mov-categoria-panel >> text=Supermarket").count() == 0
    # categoria irmã (mesmo grupo, "Alimentação"/"Food"), não tocada — continua a traduzir
    assert page.locator("#mov-categoria-panel >> text=Restaurants & Cafés").count() == 1
