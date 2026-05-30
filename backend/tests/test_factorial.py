"""Tests del adaptador Factorial (modo stub): altas, jerarquía y bajas."""
from __future__ import annotations

from app.models import Company, Employee
from app.services import factorial


def _company(db):
    c = Company(code="SN", name="Norte", autoline_company_code="01")
    db.add(c)
    db.commit()
    return c


def test_sync_creates_and_links_manager(db):
    company = _company(db)
    report = factorial.sync_employees(db, default_company_id=company.id)
    db.commit()

    assert report.created == 3
    assert report.managers_linked == 1  # Diego (E002) reporta a Lucía (E001)

    diego = db.query(Employee).filter(Employee.employee_code == "E002").one()
    lucia = db.query(Employee).filter(Employee.employee_code == "E001").one()
    assert diego.manager_id == lucia.id


def test_sync_is_idempotent(db):
    company = _company(db)
    factorial.sync_employees(db, default_company_id=company.id)
    db.commit()
    report2 = factorial.sync_employees(db, default_company_id=company.id)
    db.commit()

    assert report2.created == 0
    assert report2.updated == 3
    assert db.query(Employee).count() == 3


def test_sync_deactivates_missing_employee(db):
    company = _company(db)
    # Empleado previo con factorial_id que el stub ya no devuelve => debe darse de baja
    ghost = Employee(factorial_id="F-9999", employee_code="E900", full_name="Antiguo Empleado",
                     company_id=company.id, active=True)
    db.add(ghost)
    db.commit()

    report = factorial.sync_employees(db, default_company_id=company.id)
    db.commit()

    assert report.deactivated == 1
    db.refresh(ghost)
    assert ghost.active is False


def test_sync_preserves_accounting_data(db):
    """La sincronización no debe tocar el código contable ya configurado (employee_code estable)."""
    company = _company(db)
    factorial.sync_employees(db, default_company_id=company.id)
    db.commit()
    lucia = db.query(Employee).filter(Employee.employee_code == "E001").one()
    lucia.cost_center_id = None  # simulamos que las cuentas las gestiona contabilidad aparte
    code_before = lucia.employee_code
    db.commit()

    factorial.sync_employees(db, default_company_id=company.id)
    db.commit()
    db.refresh(lucia)
    assert lucia.employee_code == code_before  # el adapter no reescribe el código contable
