"""Regressão: apiPost/apiPut/apiDelete devolviam a Response em bruto, sem o tratamento de
sessão expirada (401) nem de falha de rede que api() (usado só para GETs) já tinha — um
POST/PUT/DELETE nestas condições falhava em silêncio para quem usa a app. Agora passam
por comSessaoERedeTratadas(), a mesma lógica de api(), com uma diferença importante: só
tratam um 401 como "sessão expirada" se já existir um TOKEN — apiPost também serve
/login e /registro, onde um 401 significa só "credenciais inválidas", não sessão nenhuma
para expirar."""


# apiPost não está em window — só lá vão as funções chamadas via onclick/onchange do HTML.
# Para a chamar directamente a partir do teste, importa-se o módulo em runtime.
_CHAMAR_API_POST = (
    'import("/static/js/utils.js").then(m => '
    'm.apiPost("/categorias", {nome: "Teste", eh_recebimento: true}).catch(() => {}))'
)


def _registar(page, live_server, email):
    page.goto(f"{live_server}/static/index.html")
    page.click("text=Criar conta")
    page.fill("#reg-nome", "Helena E2E")
    page.fill("#reg-email", email)
    page.fill("#reg-password", "senha12345")
    page.click("#btn-registo")
    page.wait_for_selector("#app-screen", state="visible")


def _interceptar_so_post(handler):
    # a app faz sempre um GET /categorias ao iniciar (iniciarApp) — sem filtrar por
    # método aqui, esse GET também seria apanhado pelo route(), criando uma corrida com
    # o POST que estes testes querem mesmo intercetar (confirmado: causava falhas
    # intermitentes até este filtro ser acrescentado).
    def wrapper(route):
        if route.request.method == "POST":
            handler(route)
        else:
            route.continue_()
    return wrapper


def test_401_num_pedido_de_escrita_autenticado_reencaminha_para_login(page, live_server):
    _registar(page, live_server, "api.401@exemplo.com")

    page.route("**/categorias", _interceptar_so_post(lambda route: route.fulfill(
        status=401, content_type="application/json",
        body='{"detail":{"code":"TOKEN_INVALIDO","message":"Token inválido ou expirado"}}',
    )))
    page.evaluate(_CHAMAR_API_POST)
    page.wait_for_selector("#auth-screen", state="visible")


def test_falha_de_rede_num_pedido_de_escrita_mostra_toast(page, live_server):
    _registar(page, live_server, "api.rede@exemplo.com")

    page.route("**/categorias", _interceptar_so_post(lambda route: route.abort("connectionfailed")))
    page.evaluate(_CHAMAR_API_POST)
    page.wait_for_selector(".toast", state="visible")
    assert "Não foi possível ligar ao servidor" in page.locator(".toast").inner_text()


def test_login_com_password_errada_nao_e_tratado_como_sessao_expirada(page, live_server):
    """O 401 de /login (credenciais erradas) não pode disparar sessaoExpirada() — não há
    sessão nenhuma nesse momento. Este cenário já era coberto por
    tests/e2e/test_auth_e2e.py::test_login_com_password_errada_mostra_erro; repetido aqui,
    a par dos outros dois testes desta ronda, para deixar explícito que é exactamente isto
    que a condição "if (TOKEN)" em comSessaoERedeTratadas protege."""
    page.goto(f"{live_server}/static/index.html")
    page.click("text=Criar conta")
    page.fill("#reg-nome", "Login E2E")
    page.fill("#reg-email", "api.login401@exemplo.com")
    page.fill("#reg-password", "senha12345")
    page.click("#btn-registo")
    page.wait_for_selector("#app-screen", state="visible")
    page.click("#avatar-wrapper")
    page.click("text=Terminar sessão")
    page.wait_for_selector("#auth-screen", state="visible")

    page.fill("#login-email", "api.login401@exemplo.com")
    page.fill("#login-password", "password-errada")
    page.click("#btn-login")

    page.wait_for_selector("#auth-erro:not(:empty)")
    assert page.is_hidden("#app-screen")
