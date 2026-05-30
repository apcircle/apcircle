"""Resolución del mapeo contable (cuenta + centro de coste + lado) por empleado/concepto."""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..enums import AccountingSide, MappingScope, PayrollConcept
from ..models import AccountingMapping, CostCenter, Employee


@dataclass
class ResolvedMapping:
    account: str
    cost_center_code: str | None
    side: AccountingSide


def resolve(db: Session, employee: Employee, concept: PayrollConcept) -> ResolvedMapping | None:
    """Busca mapeo a nivel EMPLOYEE; si no, a nivel DEPARTMENT. None si no hay configuración."""
    # Nivel empleado
    m = (
        db.query(AccountingMapping)
        .filter(
            AccountingMapping.scope == MappingScope.EMPLOYEE,
            AccountingMapping.employee_id == employee.id,
            AccountingMapping.concept == concept,
        )
        .first()
    )
    # Nivel departamento (fallback)
    if not m and employee.department_id is not None:
        m = (
            db.query(AccountingMapping)
            .filter(
                AccountingMapping.scope == MappingScope.DEPARTMENT,
                AccountingMapping.department_id == employee.department_id,
                AccountingMapping.concept == concept,
            )
            .first()
        )
    if not m:
        return None

    cc_code = None
    cc_id = m.cost_center_id or employee.cost_center_id
    if cc_id:
        cc = db.get(CostCenter, cc_id)
        cc_code = cc.code if cc else None
    return ResolvedMapping(account=m.account, cost_center_code=cc_code, side=m.side)
