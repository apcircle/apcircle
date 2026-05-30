"""Maestro de empleados y sincronización con Factorial."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..enums import Role
from ..models import Company, Employee, User
from ..schemas import CompanyOut, EmployeeCreate, EmployeeOut
from ..security import get_current_user, require_roles
from ..services import factorial

router = APIRouter(prefix="/api", tags=["maestros"])


@router.get("/companies", response_model=list[CompanyOut])
def list_companies(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Company).order_by(Company.code).all()


@router.get("/employees", response_model=list[EmployeeOut])
def list_employees(
    active: bool | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Employee)
    if active is not None:
        q = q.filter(Employee.active.is_(active))
    return q.order_by(Employee.employee_code).all()


@router.post("/employees", response_model=EmployeeOut, status_code=201)
def create_employee(
    payload: EmployeeCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.ADMIN)),
):
    emp = Employee(**payload.model_dump())
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


@router.post("/integrations/factorial/sync")
def sync_factorial(
    company_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.ADMIN)),
):
    report = factorial.sync_employees(db, default_company_id=company_id)
    if report.errors:
        # No se ha podido sincronizar: revertimos para no dejar cambios parciales.
        db.rollback()
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "; ".join(report.errors))
    db.commit()
    return {
        "mode": settings.factorial_mode,
        "created": report.created,
        "updated": report.updated,
        "deactivated": report.deactivated,
        "managers_linked": report.managers_linked,
        "pending_accounting_mapping": report.pending_mapping,
    }
