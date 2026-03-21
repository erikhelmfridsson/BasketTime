"""SMTP-utskick (t.ex. Loopia). Kräver miljövariabler MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD."""
import os
import smtplib
import sys
from email.mime.text import MIMEText
from email.utils import formataddr


def send_mail(to_addr, subject, body_text):
    """
    Skickar textmail. Returnerar True vid lyckat utskick.
    """
    server = (os.environ.get("MAIL_SERVER") or "").strip()
    if not server:
        print("MAIL_SERVER saknas – inget mail skickat.", file=sys.stderr)
        return False
    user = (os.environ.get("MAIL_USERNAME") or "").strip()
    password = os.environ.get("MAIL_PASSWORD") or ""
    sender = (os.environ.get("MAIL_DEFAULT_SENDER") or user or "").strip()
    if not sender:
        print("MAIL_DEFAULT_SENDER eller MAIL_USERNAME saknas.", file=sys.stderr)
        return False
    try:
        port = int(os.environ.get("MAIL_PORT") or "587")
    except ValueError:
        port = 587
    use_ssl = os.environ.get("MAIL_USE_SSL", "").lower() in ("1", "true", "yes")
    use_tls = os.environ.get("MAIL_USE_TLS", "true").lower() in ("1", "true", "yes")

    msg = MIMEText(body_text, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = formataddr(("BasketTime", sender))
    msg["To"] = to_addr

    try:
        if use_ssl:
            smtp = smtplib.SMTP_SSL(server, port or 465, timeout=30)
        else:
            smtp = smtplib.SMTP(server, port, timeout=30)
            if use_tls:
                smtp.starttls()
        if user:
            smtp.login(user, password)
        smtp.sendmail(sender, [to_addr], msg.as_string())
        smtp.quit()
        return True
    except Exception as e:
        print("Mailfel: %s" % (e,), file=sys.stderr)
        return False
