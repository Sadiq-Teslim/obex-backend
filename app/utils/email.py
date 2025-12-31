import smtplib, ssl
from email.message import EmailMessage
from email.utils import formataddr
from app.core.settings import settings

sender_name = settings.smtp_name
sender_email = settings.smtp_email
sender_password = settings.smtp_password

def send_email(to: str, subject: str, body: str) -> bool:
    msg = EmailMessage()
    msg.set_content(body)

    msg["From"] = formataddr((sender_name, sender_email))
    msg["To"] = to
    msg["Subject"] = subject

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False
