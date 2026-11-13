import logging
import os
import smtplib
from email.message import EmailMessage

log = logging.getLogger(__name__)


def send_mail(to: str, subject: str, body: str) -> str | None:
    mode = os.getenv("MAIL_MODE", "log").lower()
    if mode == "log":
        log.warning("HOSTELFIX MAIL TO=%s SUBJECT=%s\n%s", to, subject, body)
        return body
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_FROM", username or "noreply@iitdh.ac.in")
    if not host or not sender:
        raise RuntimeError("SMTP is not configured")
    message = EmailMessage()
    message["From"] = sender
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    with smtplib.SMTP(host, port, timeout=15) as server:
        server.starttls()
        if username and password:
            server.login(username, password)
        server.send_message(message)
    return None
