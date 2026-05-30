"""Agregados analíticos para explotación (Power BI / consumo BI)."""
from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..enums import ValidationStatus
from ..models import (
    Company,
    CostCenter,
    Department,
    Employee,
    PayrollImport,
    PayrollLine,
    PayrollPeriod,
)


def cost_by_dimension(db: Session, dimension: str, period_code: str | None = None) -> list[dict]:
    """Coste agregado por dimensión: company | cost_center | department | concept | period."""
    q = (
        db.query(PayrollLine, Employee, PayrollImport, PayrollPeriod)
        .join(PayrollImport, PayrollLine.import_id == PayrollImport.id)
        .join(PayrollPeriod, PayrollImport.period_id == PayrollPeriod.id)
        .outerjoin(Employee, PayrollLine.employee_id == Employee.id)
        .filter(PayrollLine.validation_status == ValidationStatus.OK)
    )
    if period_code:
        q = q.filter(PayrollPeriod.code == period_code)

    buckets: dict[str, float] = {}
    detail: dict[str, dict] = {}
    company_names = {c.id: c.name for c in db.query(Company).all()}
    dept_names = {d.id: d.name for d in db.query(Department).all()}
    cc_names = {c.id: c.name for c in db.query(CostCenter).all()}

    for line, emp, _imp, period in q.all():
        if dimension == "company":
            key = company_names.get(emp.company_id, "—") if emp else "—"
        elif dimension == "department":
            key = dept_names.get(emp.department_id, "—") if emp else "—"
        elif dimension == "cost_center":
            key = cc_names.get(emp.cost_center_id, "—") if emp else "—"
        elif dimension == "concept":
            key = line.concept.value
        elif dimension == "period":
            key = period.code
        else:
            key = "—"
        buckets[key] = buckets.get(key, 0.0) + float(line.amount)

    return [{"key": k, "amount": round(v, 2)} for k, v in sorted(buckets.items(), key=lambda x: -x[1])]


def fixed_vs_variable(db: Session, period_code: str | None = None) -> dict:
    """Reparto fijo vs variable (útil para análisis retributivo)."""
    from ..enums import PayrollConcept

    q = (
        db.query(PayrollLine.concept, func.sum(PayrollLine.amount))
        .join(PayrollImport, PayrollLine.import_id == PayrollImport.id)
        .join(PayrollPeriod, PayrollImport.period_id == PayrollPeriod.id)
        .filter(PayrollLine.validation_status == ValidationStatus.OK)
    )
    if period_code:
        q = q.filter(PayrollPeriod.code == period_code)
    q = q.group_by(PayrollLine.concept)

    totals = {concept: float(total or 0) for concept, total in q.all()}
    fijo = totals.get(PayrollConcept.SALARIO_FIJO, 0.0)
    variable = totals.get(PayrollConcept.SALARIO_VARIABLE, 0.0)
    ss_empresa = totals.get(PayrollConcept.SEGURIDAD_SOCIAL_EMPRESA, 0.0)
    base = fijo + variable
    return {
        "fijo": round(fijo, 2),
        "variable": round(variable, 2),
        "ss_empresa": round(ss_empresa, 2),
        "ratio_variable": round(variable / base, 4) if base else 0.0,
        "coste_total_empresa": round(base + ss_empresa, 2),
    }
