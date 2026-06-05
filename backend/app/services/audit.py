"""Registro de auditoría."""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import AuditLog


def record(
    db: Session,
    *,
    actor_id: int | None,
    action: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    meta: dict | None = None,
) -> AuditLog:
    log = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        meta=meta,
    )
    db.add(log)
    return log
