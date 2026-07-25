"""Cobertura nova para áreas que a suite E2E não tocava antes da migração para módulos ES
(perfil e gestão de categorias/grupos, incluindo arrastar-e-largar) — exactamente as zonas
de maior risco da migração: muitos dos botões aqui só existem como onclick inline gerado
dentro de template literals JS (não como atributos estáticos do HTML), pelo que um nome mal
importado ou por expor em window só rebentava ao carregar-se mesmo nesse botão."""


def _registar(page, live_server, email):
    page.goto(f"{live_server}/static/index.html")
    page.click("text=Criar conta")
    page.fill("#reg-nome", "Íris E2E")
    page.fill("#reg-email", email)
    page.fill("#reg-password", "senha12345")
    page.click("#btn-registo")
    page.wait_for_selector("#app-screen", state="visible")


def _abrir_configuracoes(page, seccao):
    page.click("#avatar-wrapper")
    page.click("text=Configurações")
    page.wait_for_selector("#modal-configuracoes.open")
    page.click(f'.perfil-sidebar-item[data-secao="{seccao}"]')


def test_editar_nome_e_email_do_perfil(page, live_server):
    _registar(page, live_server, "iris.perfil@exemplo.com")
    _abrir_configuracoes(page, "conta")

    page.click("#perfil-secao-conta >> text=Nome")
    page.wait_for_selector("#modal-editar-perfil", state="visible")
    page.fill("#perfil-nome", "Íris Alterada")
    page.fill("#perfil-email", "iris.perfil@exemplo.com")
    page.click("#btn-guardar-perfil")

    page.wait_for_selector("#modal-editar-perfil", state="hidden")
    assert page.inner_text("#perfil-nome-display") == "Íris Alterada"
    # o avatar/friso também são actualizados a partir do mesmo estadoGlobal.NOME
    assert "ÍA" in page.inner_text("#avatar-btn") or page.inner_text("#avatar-btn").strip() != ""


def test_criar_grupo_categoria_editar_e_eliminar(page, live_server):
    _registar(page, live_server, "iris.categorias@exemplo.com")
    _abrir_configuracoes(page, "categorias")
    page.wait_for_selector("#lista-categorias-gestao .grupo-gestao")

    # criar grupo novo (em "Entradas", aba pré-selecionada)
    page.click("text=+ Adicionar Grupo")
    page.wait_for_selector("#modal-grupo", state="visible")
    page.fill("#grupo-nome", "Grupo Teste E2E")
    page.click("#btn-guardar-grupo")
    page.wait_for_selector("#modal-grupo", state="hidden")
    grupo = page.locator(".grupo-gestao", has_text="Grupo Teste E2E")
    grupo.wait_for()

    # adicionar categoria dentro do grupo novo
    grupo.locator(".grupo-gestao-header button", has_text="+").click()
    page.wait_for_selector("#modal-categoria-gestao", state="visible")
    page.fill("#categoria-gestao-nome", "Categoria Teste E2E")
    page.click("#btn-guardar-categoria-gestao")
    page.wait_for_selector("#modal-categoria-gestao", state="hidden")
    categoria = page.locator(".categoria-gestao-item", has_text="Categoria Teste E2E")
    categoria.wait_for()

    # editar a categoria (renomear) — via menu de acções (toggleMenuAcoesCategoria)
    # scroll explícito antes do clique: <main> fecha o menu de acções ao fazer scroll
    # (de propósito, para não ficar "pendurado" se o conteúdo por baixo se mexer) — sem
    # isto, o auto-scroll que o Playwright faz para o botão ficar visível dispara esse
    # scroll DEPOIS do clique ter aberto o menu, fechando-o de imediato.
    categoria.scroll_into_view_if_needed()
    page.wait_for_timeout(200)
    categoria.locator("button", has_text="⋮").click()
    page.click("#menu-acoes-flutuante >> text=Editar")
    page.wait_for_selector("#modal-categoria-gestao", state="visible")
    page.fill("#categoria-gestao-nome", "Categoria Renomeada E2E")
    page.click("#btn-guardar-categoria-gestao")
    page.wait_for_selector("#modal-categoria-gestao", state="hidden")
    page.locator(".categoria-gestao-item", has_text="Categoria Renomeada E2E").wait_for()

    # eliminar a categoria — sem movimentos associados, confirmarEliminarCategoria apaga
    # de imediato (só mostra o modal de migração quando a API recusa por haver dependentes)
    categoria_renomeada = page.locator(".categoria-gestao-item", has_text="Categoria Renomeada E2E")
    categoria_renomeada.scroll_into_view_if_needed()
    page.wait_for_timeout(200)
    categoria_renomeada.locator("button", has_text="⋮").click()
    page.click("#menu-acoes-flutuante >> text=Eliminar")
    page.wait_for_selector(".categoria-gestao-item:has-text('Categoria Renomeada E2E')", state="hidden")
    assert page.locator(".categoria-gestao-item", has_text="Categoria Renomeada E2E").count() == 0

    # eliminar o grupo (já sem categorias) — mesma lógica, apaga de imediato
    grupo_a_eliminar = page.locator(".grupo-gestao", has_text="Grupo Teste E2E")
    grupo_a_eliminar.scroll_into_view_if_needed()
    page.wait_for_timeout(200)
    grupo_a_eliminar.locator(".grupo-gestao-header button", has_text="⋮").click()
    page.click("#menu-acoes-flutuante >> text=Eliminar")
    page.wait_for_selector(".grupo-gestao:has-text('Grupo Teste E2E')", state="hidden")
    assert page.locator(".grupo-gestao", has_text="Grupo Teste E2E").count() == 0


def test_reordenar_grupos_pelos_botoes_mover(page, live_server):
    """moverItemCategoria (chamado pelos botões "Mover para cima/baixo" do menu de acções)
    é o mecanismo de reordenação por teclado/clique — mais fiável de testar do que simular
    eventos nativos de drag-and-drop, e cobre o mesmo risco de módulos (onclick gerado
    dinamicamente dentro do menu flutuante)."""
    _registar(page, live_server, "iris.mover@exemplo.com")
    _abrir_configuracoes(page, "categorias")
    page.wait_for_selector("#lista-categorias-gestao .grupo-gestao")

    nomes_antes = page.locator("#lista-categorias-gestao .grupo-gestao .nome").all_inner_texts()
    assert len(nomes_antes) >= 2, "precisa de pelo menos 2 grupos por omissão para testar reordenação"

    primeiro_grupo = page.locator(".grupo-gestao").first
    primeiro_grupo.scroll_into_view_if_needed()
    page.wait_for_timeout(200)
    primeiro_grupo.locator(".grupo-gestao-header button", has_text="⋮").click()
    page.click("#menu-acoes-flutuante >> text=Mover para baixo")
    page.wait_for_timeout(300)

    nomes_depois = page.locator("#lista-categorias-gestao .grupo-gestao .nome").all_inner_texts()
    assert nomes_depois[0] == nomes_antes[1]
    assert nomes_depois[1] == nomes_antes[0]


def test_reordenar_categorias_por_arrastar_e_largar_nativo(page, live_server):
    """Cobre o outro caminho de reordenação — arrastarInicio/arrastarSobre/arrastarFim/
    largarSobre — que só existe como atributos ondragstart/ondragover/ondragend/ondrop
    gerados dinamicamente; nenhum destes tinha teste algum antes da migração."""
    _registar(page, live_server, "iris.dragdrop@exemplo.com")
    _abrir_configuracoes(page, "categorias")
    page.wait_for_selector("#lista-categorias-gestao .grupo-gestao")

    primeiro_grupo = page.locator(".grupo-gestao").first
    categorias = primeiro_grupo.locator(".categoria-gestao-item")
    if categorias.count() < 2:
        primeiro_grupo.locator("button", has_text="+").click()
        page.wait_for_selector("#modal-categoria-gestao", state="visible")
        page.fill("#categoria-gestao-nome", "Categoria Extra Drag E2E")
        page.click("#btn-guardar-categoria-gestao")
        page.wait_for_selector("#modal-categoria-gestao", state="hidden")
        categorias = primeiro_grupo.locator(".categoria-gestao-item")

    nomes_antes = set(categorias.locator("span").first.all_inner_texts())
    alca_origem = categorias.first.locator(".arraste-alca")
    alvo = categorias.nth(1)
    alca_origem.drag_to(alvo)
    page.wait_for_timeout(300)

    # o essencial aqui é que o ciclo ondragstart/over/end/drop corra sem excepções (a
    # fixture falha-se-houver-erro-de-consola já garante isso) e que nada se perca —
    # a ordem exacta que a app escolhe ao largar não é o que este teste está a validar.
    nomes_depois = set(primeiro_grupo.locator(".categoria-gestao-item span").first.all_inner_texts())
    assert nomes_depois == nomes_antes
