"""Máquina de estados del periodo de nómina. Ver docs/03-flujo-y-roles.md."""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..enums import PeriodStatus
from ..models import PayrollPeriod, StateTransition
from . import audit

S = PeriodStatus

ALLOWED_TRANSITIONS: dict[PeriodStatus, set[PeriodStatus]] = {
    S.DRAFT: {S.COMMISSIONS_IMPORTED},
    S.COMMISSIONS_IMPORTED: {S.PENDING_MANAGER_APPROVAL, S.COMMISSIONS_IMPORTED},
    S.PENDING_MANAGER_APPROVAL: {S.MANAGER_APPROVED, S.COMMISSIONS_IMPORTED},  # rechazo => atrás
    S.MANAGER_APPROVED: {S.HR_APPROVED, S.PENDING_MANAGER_APPROVAL},
    S.HR_APPROVED: {S.SENT_TO_GESTORIA, S.MANAGER_APPROVED},
    S.SENT_TO_GESTORIA: {S.PAYROLL_RECEIVED},
    S.PAYROLL_RECEIVED: {S.PAYROLL_VALIDATED, S.PAYROLL_RECEIVED},
    S.PAYROLL_VALIDATED: {S.JOURNAL_GENERATED, S.PAYROLL_RECEIVED},
    S.JOURNAL_GENERATED: {S.CLOSED, S.PAYROLL_VALIDATED},
    S.CLOSED: set(),
}


def can_transition(current: PeriodStatus, target: PeriodStatus) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())


def transition(
    db: Session,
    period: PayrollPeriod,
    target: PeriodStatus,
    *,
    actor_id: int | None,
    note: str | None = None,
) -> PayrollPeriod:
    if not can_transition(period.status, target):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Transición no permitida: {period.status.value} → {target.value}",
        )
    db.add(
        StateTransition(
            period_id=period.id,
            from_status=period.status,
            to_status=target,
            actor_id=actor_id,
            note=note,
        )
    )
    audit.record(
        db,
        actor_id=actor_id,
        action="period.transition",
        entity_type="PayrollPeriod",
        entity_id=period.id,
        meta={"from": period.status.value, "to": target.value, "note": note},
    )
    period.status = target
    return period
