"""Regressão: as 15 funções do painel de "Ordenar" (Contas/Movimentos/Recorrentes, cada
uma com a sua cópia quase idêntica) foram consolidadas numa implementação parametrizada
(PREFIXOS_ORDENAR + renderizarPainelOrdenar/selecionarCampoOrdenar/selecionarDirecaoOrdenar/
toggleOrdenar/fecharOrdenar). Este teste confirma que os três painéis continuam a abrir,
listar os campos certos e aplicar a escolha, num browser real e no viewport móvel onde
este painel (".ordenacao-mobile") é visível."""


def _registar(page, live_server, email):
    page.goto(f"{live_server}/static/index.html")
    page.click("text=Criar conta")
    page.fill("#reg-nome", "Fátima E2E")
    page.fill("#reg-email", email)
    page.fill("#reg-password", "senha12345")
    page.click("#btn-registo")
    page.wait_for_selector("#app-screen", state="visible")


def _ir_para(page, pagina):
    page.click(".barra-mobile-topo button")
    page.click(f'.friso-item[data-pagina="{pagina}"]')
    # no mobile o menu fica sobreposto ao conteúdo até ser fechado explicitamente
    page.evaluate('document.getElementById("friso").classList.remove("expandido")')


def test_paineis_de_ordenar_contas_movimentos_recorrentes(page, live_server):
    page.set_viewport_size({"width": 390, "height": 844})
    _registar(page, live_server, "ordenacao.e2e@exemplo.com")

    page.wait_for_selector("#page-contas.active")
    page.click("#ct-ordenar-btn")
    page.wait_for_selector("#ct-ordenar-panel.aberto")
    assert page.locator("#ct-ordenar-campos").inner_text().split("\n") == ["Nome", "Saldo Atual", "Data Início"]
    page.click("#ct-ordenar-campos >> text=Saldo Atual")
    assert page.locator("#ct-ordenar-btn-texto").inner_text() == "Ordenar: Saldo Atual"

    _ir_para(page, "movimentos")
    page.wait_for_selector("#page-movimentos.active")
    page.click("#mov-ordenar-btn")
    page.wait_for_selector("#mov-ordenar-panel.aberto")
    assert page.locator("#mov-ordenar-campos").inner_text().split("\n") == ["Data", "Valor", "Descrição"]
    page.click("#mov-ordenar-campos >> text=Valor")
    assert page.locator("#mov-ordenar-btn-texto").inner_text() == "Ordenar: Valor"

    _ir_para(page, "analise")
    page.wait_for_selector("#page-analise.active")
    page.click('.analise-tab[data-aba="recorrencias"]')
    page.wait_for_selector("#analise-secao-recorrencias.active")
    page.click("#an-recorrentes-ordenar-btn")
    page.wait_for_selector("#an-recorrentes-ordenar-panel.aberto")
    assert page.locator("#an-recorrentes-ordenar-campos").inner_text().split("\n") == [
        "Valor Médio", "Frequência", "Próxima Data",
    ]
    page.click("#an-recorrentes-ordenar-campos >> text=Frequência")
    assert page.locator("#an-recorrentes-ordenar-btn-texto").inner_text() == "Ordenar: Frequência"
