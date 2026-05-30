"""Fixtures de test: BD SQLite aislada en memoria + maestros mínimos."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.enums import (
    AccountingSide,
    DEFAULT_CONCEPT_ACCOUNT,
    DEFAULT_CONCEPT_SIDE,
    MappingScope,
    PayrollConcept,
)
from app.models import AccountingMapping, Company, CostCenter, Department, Employee


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, future=True)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def master(db):
    """Crea una sociedad, departamento, centro de coste, empleado y mapeos contables."""
    company = Company(code="SN", name="Norte", autoline_company_code="01")
    db.add(company); db.flush()
    cc = CostCenter(company_id=company.id, code="VN", name="Ventas VN")
    db.add(cc); db.flush()
    dept = Department(company_id=company.id, name="Ventas", default_cost_center_id=cc.id)
    db.add(dept); db.flush()
    emp = Employee(employee_code="E001", full_name="Lucía Marín", company_id=company.id,
                   department_id=dept.id, cost_center_id=cc.id)
    db.add(emp); db.flush()
    for concept in PayrollConcept:
        db.add(AccountingMapping(
            scope=MappingScope.DEPARTMENT, department_id=dept.id, concept=concept,
            account=DEFAULT_CONCEPT_ACCOUNT[concept],
            cost_center_id=cc.id if DEFAULT_CONCEPT_SIDE[concept] == AccountingSide.DEBIT else None,
            side=DEFAULT_CONCEPT_SIDE[concept],
        ))
    db.commit()
    return {"company": company, "dept": dept, "cc": cc, "emp": emp}
