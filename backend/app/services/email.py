"""Servicio de envío de correo. Modo real (SMTP) o modo registro si no hay SMTP."""
from __future__ import annotations

import smtplib
from email.message import EmailMessage
from pathlib import Path

from sqlalchemy.orm import Session

from ..config import settings
from . import audit


def send(
    db: Session,
    *,
    to: str,
    subject: str,
    body: str,
    attachment: Path | None = None,
    actor_id: int | None = None,
) -> bool:
    """Envía un correo. Devuelve True si se envió por SMTP, False si solo se registró (demo)."""
    sent = False
    if settings.smtp_host:
        msg = EmailMessage()
        msg["From"] = settings.smtp_from
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        if attachment and attachment.exists():
            data = attachment.read_bytes()
            msg.add_attachment(
                data,
                maintype="application",
                subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                filename=attachment.name,
            )
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if settings.smtp_tls:
                server.starttls()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password or "")
            server.send_message(msg)
        sent = True

    audit.record(
        db,
        actor_id=actor_id,
        action="email.send" if sent else "email.logged",
        entity_type="Email",
        meta={"to": to, "subject": subject, "attachment": attachment.name if attachment else None, "sent": sent},
    )
    return sent
