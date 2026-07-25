"""Envio de email por SMTP — hoje só usado para o link de recuperação de password (ver
routers/auth.py::esqueci_password, via BackgroundTasks)."""

import logging
import smtplib
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def enviar_email(destinatario: str, assunto: str, corpo: str) -> None:
    """Corre em background (ver BackgroundTasks em routers/auth.py) — uma excepção aqui
    não chega a lado nenhum sozinha, por isso apanhamo-la e registamo-la nós próprios;
    sem isto, uma falha de SMTP (credenciais erradas, EMAIL_APP_PASSWORD em falta, rede
    em baixo) ficava invisível."""
    msg = MIMEText(corpo)
    msg["Subject"] = assunto
    msg["From"] = settings.EMAIL_REMETENTE
    msg["To"] = destinatario

    try:
        with smtplib.SMTP_SSL(settings.EMAIL_SMTP_HOST, settings.EMAIL_SMTP_PORT) as servidor:
            servidor.login(settings.EMAIL_REMETENTE, settings.EMAIL_APP_PASSWORD)
            servidor.send_message(msg)
    except Exception:
        logger.exception("Falha ao enviar email para %s", destinatario)
