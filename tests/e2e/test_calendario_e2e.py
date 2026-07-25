"""Regressão: os calendários de data única e de intervalo tinham cada um a sua cópia
quase idêntica de navegação de mês/ano e reposicionamento (~230 linhas ao todo). Foram
consolidados em 4 funções parametrizadas por tipo ("simples" | "range") — ver
TIPOS_CALENDARIO em static/index.html. Nenhum dos dois tinha teste algum antes disto."""


def _registar(page, live_server, email):
    page.goto(f"{live_server}/static/index.html")
    page.click("text=Criar conta")
    page.fill("#reg-nome", "Gabriela E2E")
    page.fill("#reg-email", email)
    page.fill("#reg-password", "senha12345")
    page.click("#btn-registo")
    page.wait_for_selector("#app-screen", state="visible")


def test_calendario_simples_navega_e_seleciona_dia(page, live_server):
    _registar(page, live_server, "calendario.simples@exemplo.com")
    page.evaluate("abrirModalMovimento()")
    page.wait_for_selector("#modal-movimento", state="visible")

    page.click("#mov-data-wrapper")
    page.wait_for_selector('#calendario-panel[style*="display: block"]')
    assert page.locator("#calendario-panel .cal-dia:not(.cal-vazio)").count() > 20

    # navegar para o mês anterior continua a mostrar uma grelha válida
    page.click("#calendario-panel .cal-nav >> nth=0")
    assert page.locator("#calendario-panel .cal-dia:not(.cal-vazio)").count() > 20

    # escolher mês/ano pelos <select> e depois um dia — fecha o painel e preenche o campo
    page.select_option("#calendario-panel select >> nth=0", "0")   # Janeiro
    page.select_option("#calendario-panel select >> nth=1", "2020")
    page.click("#calendario-panel .cal-dia:not(.cal-vazio):not(.desabilitado) >> nth=10")

    assert page.locator("#calendario-panel").evaluate('el => el.style.display') == "none"
    assert "01-2020" in page.input_value("#mov-data") or "2020" in page.input_value("#mov-data")


def test_calendario_range_presets_e_selecao_manual(page, live_server):
    _registar(page, live_server, "calendario.range@exemplo.com")
    page.click('.friso-item[data-pagina="movimentos"]')
    page.wait_for_selector("#page-movimentos.active")

    page.click("#mov-periodo-wrapper")
    page.wait_for_selector('#calendario-range-panel[style*="display: flex"]')
    assert page.locator(".cal-range-preset").count() == 6

    page.click(".cal-range-preset >> text=Este mês")
    assert page.locator("#calendario-range-panel").evaluate('el => el.style.display') == "none"
    assert "—" in page.input_value("#mov-periodo")

    # selecção manual de um intervalo (dois cliques): o primeiro define só o início
    page.click("#mov-periodo-wrapper")
    page.wait_for_selector('#calendario-range-panel[style*="display: flex"]')
    dias = page.locator("#calendario-range-panel .cal-dia:not(.cal-vazio):not(.desabilitado)")
    dias.nth(2).click()
    assert "escolhe o fim" in page.locator(".cal-range-resumo").inner_text()
    assert page.locator("#calendario-range-panel").evaluate('el => el.style.display') == "flex"

    dias_apos_primeiro_clique = page.locator("#calendario-range-panel .cal-dia:not(.cal-vazio):not(.desabilitado)")
    dias_apos_primeiro_clique.nth(5).click()
    assert page.locator("#calendario-range-panel").evaluate('el => el.style.display') == "none"
    assert "—" in page.input_value("#mov-periodo")
