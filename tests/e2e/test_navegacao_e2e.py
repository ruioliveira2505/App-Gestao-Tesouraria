"""Regressão: atualizarPosicoesFixasContas/Movimentos/Analise eram três funções idênticas
(uma por página), cada uma com o seu próprio ResizeObserver — foram consolidadas numa só
função parametrizada (atualizarPosicoesFixas(idPagina)) com um único ResizeObserver
partilhado. Este teste garante que a consolidação não partiu o posicionamento sticky do
cabeçalho de filtros ao navegar entre as três páginas que o usam."""


def _registar_e_entrar(page, live_server, email):
    page.goto(f"{live_server}/static/index.html")
    page.click("text=Criar conta")
    page.fill("#reg-nome", "Diana E2E")
    page.fill("#reg-email", email)
    page.fill("#reg-password", "senha12345")
    page.click("#btn-registo")
    page.wait_for_selector("#app-screen", state="visible")


def test_posicoes_fixas_dos_filtros_ao_navegar_entre_paginas(page, live_server):
    _registar_e_entrar(page, live_server, "diana.e2e@exemplo.com")

    for pagina, seletor_pagina in [
        ("contas", "#page-contas"),
        ("movimentos", "#page-movimentos"),
        ("analise", "#page-analise"),
    ]:
        page.click(f'.friso-item[data-pagina="{pagina}"]')
        page.wait_for_selector(f"{seletor_pagina}.active")
        filtros = page.locator(f"{seletor_pagina} .filtros")
        # atualizarPosicoesFixas() corre num setTimeout(0) — espera até o "top" ser aplicado
        page.wait_for_function(
            """(sel) => {
                const el = document.querySelector(sel);
                return el && el.style.top !== "";
            }""",
            arg=f"{seletor_pagina} .filtros",
        )
        assert filtros.evaluate("el => el.style.top") != ""
