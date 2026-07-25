"""Regressão: a pesquisa de movimentos reconstruía a tabela a cada tecla premida, sem
debounce. `renderizarTabelaMovimentosDebounced` (wrapper com debounce de 250ms) passou a
ligar-se ao campo de pesquisa — este teste confirma que a filtragem continua correcta
depois da pausa, não só que deixou de correr a cada tecla."""


def test_pesquisa_de_movimentos_filtra_apos_debounce(page, live_server):
    page.goto(f"{live_server}/static/index.html")
    page.click("text=Criar conta")
    page.fill("#reg-nome", "Elsa E2E")
    page.fill("#reg-email", "elsa.e2e@exemplo.com")
    page.fill("#reg-password", "senha12345")
    page.click("#btn-registo")
    page.wait_for_selector("#app-screen", state="visible")

    page.click('.friso-item[data-pagina="movimentos"]')
    page.wait_for_selector("#page-movimentos.active")
    page.wait_for_selector("#tabela-movimentos")

    page.fill("#filtro-pesquisa", "zzz-descricao-que-nao-existe")
    page.wait_for_timeout(400)
    assert "Nenhum movimento encontrado" in page.locator("#tabela-movimentos").inner_text()

    page.fill("#filtro-pesquisa", "")
    page.wait_for_timeout(400)
    assert "Ainda não tens movimentos" in page.locator("#tabela-movimentos").inner_text()
