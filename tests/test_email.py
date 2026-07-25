from app.services.email import enviar_email


def test_enviar_email_com_falha_smtp_nao_propaga(monkeypatch, caplog):
    """enviar_email corre em BackgroundTasks — uma excepção que escape daqui não chega a
    lado nenhum sozinha, por isso tem de ser apanhada e registada, nunca propagada."""
    class SMTPFalso:
        def __enter__(self):
            raise ConnectionError("falha propositada de rede")

        def __exit__(self, *args):
            pass

    monkeypatch.setattr("smtplib.SMTP_SSL", lambda *a, **k: SMTPFalso())

    with caplog.at_level("ERROR"):
        enviar_email("alguem@exemplo.com", "Assunto", "Corpo")

    assert "Falha ao enviar email" in caplog.text


def test_enviar_email_com_sucesso_faz_login_e_envia_a_mensagem(monkeypatch):
    """Só o caminho de falha estava testado — isto confirma que, quando o SMTP funciona,
    enviar_email chega mesmo a autenticar-se e a enviar a mensagem (não só que uma
    excepção não propaga)."""
    chamadas = []

    class SMTPFalso:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def login(self, utilizador, password):
            chamadas.append(("login", utilizador, password))

        def send_message(self, msg):
            chamadas.append(("send_message", msg))

    monkeypatch.setattr("smtplib.SMTP_SSL", lambda *a, **k: SMTPFalso())

    enviar_email("alguem@exemplo.com", "Assunto", "Corpo")

    assert [c[0] for c in chamadas] == ["login", "send_message"]
    assert chamadas[1][1]["To"] == "alguem@exemplo.com"
    assert chamadas[1][1]["Subject"] == "Assunto"
