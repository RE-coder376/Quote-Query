# -*- coding: utf-8 -*-
import html
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

ROOT = Path(r"C:\Users\User\Documents\Projects\AI_Chatbot")
HERE = Path(r"C:\Users\User\Documents\Projects\Quote Querry\outreach")
PACKAGE = HERE / "ANCHORWIN_CONTEXT_FIX_WAME_20260730.md"
RECIPIENT = "hamzanaimt.14@gmail.com"


def env_value(name: str) -> str:
    env_path = ROOT / ".env"
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{name}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


config = json.loads((ROOT / "config.json").read_text(encoding="utf-8-sig"))
sender = config["contact_email"]
smtp_password = env_value("SMTP_PASSWORD")
plain = PACKAGE.read_text(encoding="utf-8")

subject = "Anchorwin wa.me link with corrected message"
html_body = (
    "<div style='font-family:Arial,sans-serif;line-height:1.6;max-width:820px;color:#222'>"
    "<h2 style='margin-bottom:6px'>Anchorwin wa.me link with corrected message</h2>"
    "<pre style='white-space:pre-wrap;font:13px/1.5 Consolas,monospace;background:#f5f7fa;padding:16px;border-radius:8px'>"
    + html.escape(plain)
    + "</pre></div>"
)

email = MIMEMultipart("alternative")
email["Subject"] = subject
email["From"] = sender
email["To"] = RECIPIENT
email.attach(MIMEText(plain, "plain", "utf-8"))
email.attach(MIMEText(html_body, "html", "utf-8"))

with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
    smtp.login(sender, smtp_password)
    smtp.sendmail(sender, [RECIPIENT], email.as_string())

print(json.dumps({"sent": True, "to": RECIPIENT, "subject": subject, "package": str(PACKAGE)}))
