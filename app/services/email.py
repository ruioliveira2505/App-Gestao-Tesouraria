import smtplib
from email.mime.text import MIMEText

from app.core.config import settings


def enviar_email(destinatario, assunto, corpo):
    msg = MIMEText(corpo)
    msg["Subject"] = assunto
    msg["From"] = settings.EMAIL_REMETENTE
    msg["To"] = destinatario

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
        servidor.login(settings.EMAIL_REMETENTE, settings.EMAIL_APP_PASSWORD)
        servidor.send_message(msg)
