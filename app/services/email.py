import smtplib
import os
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
EMAIL_PASSWORD  = os.getenv("EMAIL_APP_PASSWORD")


def enviar_email(destinatario, assunto, corpo):
    msg = MIMEText(corpo)
    msg["Subject"] = assunto
    msg["From"] = EMAIL_REMETENTE
    msg["To"] = destinatario

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
        servidor.login(EMAIL_REMETENTE, EMAIL_PASSWORD)
        servidor.send_message(msg)