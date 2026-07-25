"""Primeiro teste E2E — prova que a infra-estrutura (live_server + Playwright) funciona
a sério antes de escrever testes para os problemas já identificados no roteiro."""

import re


def test_registo_e_login_pela_interface(page, live_server):
    page.goto(f"{live_server}/static/index.html")

    # separador "Criar conta"
    page.click("text=Criar conta")
    page.fill("#reg-nome", "Ana E2E")
    page.fill("#reg-email", "ana.e2e@exemplo.com")
    page.fill("#reg-password", "senha12345")
    page.click("#btn-registo")

    # depois de um registo com sucesso, a app mostra o ecrã principal (#app-screen)
    # e deixa de mostrar o de autenticação (#auth-screen)
    page.wait_for_selector("#app-screen", state="visible")
    assert page.is_hidden("#auth-screen")

    # sessão fica em localStorage — um refresh não devia voltar ao ecrã de login
    page.reload()
    page.wait_for_selector("#app-screen", state="visible")

    # logout (menu do avatar → "Terminar sessão") devolve ao ecrã de autenticação
    page.click("#avatar-wrapper")
    page.click("text=Terminar sessão")
    page.wait_for_selector("#auth-screen", state="visible")

    # login com a conta acabada de criar
    page.fill("#login-email", "ana.e2e@exemplo.com")
    page.fill("#login-password", "senha12345")
    page.click("#btn-login")
    page.wait_for_selector("#app-screen", state="visible")


def test_login_com_password_errada_mostra_erro(page, live_server):
    page.goto(f"{live_server}/static/index.html")
    page.click("text=Criar conta")
    page.fill("#reg-nome", "Bruno E2E")
    page.fill("#reg-email", "bruno.e2e@exemplo.com")
    page.fill("#reg-password", "senha12345")
    page.click("#btn-registo")
    page.wait_for_selector("#app-screen", state="visible")
    page.click("#avatar-wrapper")
    page.click("text=Terminar sessão")
    page.wait_for_selector("#auth-screen", state="visible")

    page.fill("#login-email", "bruno.e2e@exemplo.com")
    page.fill("#login-password", "password-errada")
    page.click("#btn-login")

    page.wait_for_selector("#auth-erro:not(:empty)")
    erro = page.inner_text("#auth-erro")
    assert re.search(r"incorret", erro, re.IGNORECASE)
    assert page.is_hidden("#app-screen")


def test_logout_a_partir_do_separador_registo_repoe_o_separador_login(page, live_server):
    """Regressão: logout() não repunha o separador "Entrar" — se saísses a partir do
    separador "Criar conta", o ecrã de autenticação voltava a mostrar-se nesse separador
    em vez do de login. Corrigido chamando trocarTab("login") em logout()."""
    page.goto(f"{live_server}/static/index.html")
    page.click("text=Criar conta")
    page.fill("#reg-nome", "Carla E2E")
    page.fill("#reg-email", "carla.e2e@exemplo.com")
    page.fill("#reg-password", "senha12345")
    page.click("#btn-registo")
    page.wait_for_selector("#app-screen", state="visible")

    page.click("#avatar-wrapper")
    page.click("text=Terminar sessão")
    page.wait_for_selector("#auth-screen", state="visible")

    assert page.is_visible("#tab-login")
    assert page.is_hidden("#tab-registo")
