"""Modelo de datos SQLAlchemy. Ver docs/02-modelo-datos.md."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    JSON,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base
from .enums import (
    AccountingSide,
    ApprovalDecision,
    ApprovalLevel,
    MappingScope,
    PayrollConcept,
    PeriodStatus,
    Role,
    ValidationStatus,
)


class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    tax_id: Mapped[str | None] = mapped_column(String(20))
    autoline_company_code: Mapped[str] = mapped_column(String(10), default="01")

    cost_centers: Mapped[list["CostCenter"]] = relationship(back_populates="company")
    departments: Mapped[list["Department"]] = relationship(back_populates="company")


class CostCenter(Base):
    __tablename__ = "cost_centers"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    code: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(120))

    company: Mapped[Company] = relationship(back_populates="cost_centers")


class Department(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    name: Mapped[str] = mapped_column(String(120))
    default_cost_center_id: Mapped[int | None] = mapped_column(ForeignKey("cost_centers.id"))

    company: Mapped[Company] = relationship(back_populates="departments")
    default_cost_center: Mapped[CostCenter | None] = relationship()


class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(primary_key=True)
    factorial_id: Mapped[str | None] = mapped_column(String(40), index=True)
    employee_code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160))
    national_id: Mapped[str | None] = mapped_column(String(20), index=True)
    email: Mapped[str | None] = mapped_column(String(160))

    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    cost_center_id: Mapped[int | None] = mapped_column(ForeignKey("cost_centers.id"))
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))

    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    company: Mapped[Company] = relationship()
    department: Mapped[Department | None] = relationship()
    cost_center: Mapped[CostCenter | None] = relationship()
    manager: Mapped["Employee | None"] = relationship(remote_side="Employee.id")
    mappings: Mapped[list["AccountingMapping"]] = relationship(back_populates="employee")


class AccountingMapping(Base):
    """Cuenta contable + centro de coste para un concepto, a nivel empleado o departamento."""

    __tablename__ = "accounting_mappings"
    id: Mapped[int] = mapped_column(primary_key=True)
    scope: Mapped[MappingScope] = mapped_column(Enum(MappingScope))
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    concept: Mapped[PayrollConcept] = mapped_column(Enum(PayrollConcept))
    account: Mapped[str] = mapped_column(String(20))
    cost_center_id: Mapped[int | None] = mapped_column(ForeignKey("cost_centers.id"))
    side: Mapped[AccountingSide] = mapped_column(Enum(AccountingSide))

    employee: Mapped[Employee | None] = relationship(back_populates="mappings")
    department: Mapped[Department | None] = relationship()
    cost_center: Mapped[CostCenter | None] = relationship()


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Ámbito de un MANAGER (nullable => ámbito global)
    scope_company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"))
    scope_department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))

    scope_company: Mapped[Company | None] = relationship()
    scope_department: Mapped[Department | None] = relationship()


class PayrollPeriod(Base):
    __tablename__ = "payroll_periods"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), index=True)  # 2026-05
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"))  # null => grupo
    status: Mapped[PeriodStatus] = mapped_column(Enum(PeriodStatus), default=PeriodStatus.DRAFT)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    company: Mapped[Company | None] = relationship()
    commission_imports: Mapped[list["CommissionImport"]] = relationship(back_populates="period")
    payroll_imports: Mapped[list["PayrollImport"]] = relationship(back_populates="period")
    approvals: Mapped[list["Approval"]] = relationship(back_populates="period")
    transitions: Mapped[list["StateTransition"]] = relationship(back_populates="period")
    journal_entries: Mapped[list["JournalEntry"]] = relationship(back_populates="period")


class CommissionImport(Base):
    __tablename__ = "commission_imports"
    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("payroll_periods.id"))
    filename: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str] = mapped_column(String(500))
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    row_count: Mapped[int] = mapped_column(default=0)

    period: Mapped[PayrollPeriod] = relationship(back_populates="commission_imports")
    lines: Mapped[list["CommissionLine"]] = relationship(back_populates="import_", cascade="all, delete-orphan")


class CommissionLine(Base):
    __tablename__ = "commission_lines"
    id: Mapped[int] = mapped_column(primary_key=True)
    import_id: Mapped[int] = mapped_column(ForeignKey("commission_imports.id"))
    employee_code: Mapped[str] = mapped_column(String(40))
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    department: Mapped[str | None] = mapped_column(String(120))
    concept: Mapped[str] = mapped_column(String(60))
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    notes: Mapped[str | None] = mapped_column(Text)
    validation_status: Mapped[ValidationStatus] = mapped_column(Enum(ValidationStatus), default=ValidationStatus.PENDING)

    import_: Mapped[CommissionImport] = relationship(back_populates="lines")
    employee: Mapped[Employee | None] = relationship()


class PayrollImport(Base):
    __tablename__ = "payroll_imports"
    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("payroll_periods.id"))
    filename: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str] = mapped_column(String(500))
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    row_count: Mapped[int] = mapped_column(default=0)

    period: Mapped[PayrollPeriod] = relationship(back_populates="payroll_imports")
    lines: Mapped[list["PayrollLine"]] = relationship(back_populates="import_", cascade="all, delete-orphan")


class PayrollLine(Base):
    __tablename__ = "payroll_lines"
    id: Mapped[int] = mapped_column(primary_key=True)
    import_id: Mapped[int] = mapped_column(ForeignKey("payroll_imports.id"))
    employee_code: Mapped[str] = mapped_column(String(40))
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    concept: Mapped[PayrollConcept] = mapped_column(Enum(PayrollConcept))
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    validation_status: Mapped[ValidationStatus] = mapped_column(Enum(ValidationStatus), default=ValidationStatus.PENDING)
    validation_message: Mapped[str | None] = mapped_column(String(255))

    import_: Mapped[PayrollImport] = relationship(back_populates="lines")
    employee: Mapped[Employee | None] = relationship()


class Approval(Base):
    __tablename__ = "approvals"
    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("payroll_periods.id"))
    level: Mapped[ApprovalLevel] = mapped_column(Enum(ApprovalLevel))
    approver_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    scope_company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"))
    scope_department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    decision: Mapped[ApprovalDecision] = mapped_column(Enum(ApprovalDecision))
    comment: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    period: Mapped[PayrollPeriod] = relationship(back_populates="approvals")
    approver: Mapped[User | None] = relationship()


class StateTransition(Base):
    __tablename__ = "state_transitions"
    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("payroll_periods.id"))
    from_status: Mapped[PeriodStatus] = mapped_column(Enum(PeriodStatus))
    to_status: Mapped[PeriodStatus] = mapped_column(Enum(PeriodStatus))
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    note: Mapped[str | None] = mapped_column(Text)

    period: Mapped[PayrollPeriod] = relationship(back_populates="transitions")


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("payroll_periods.id"))
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"))
    entry_date: Mapped[date] = mapped_column(Date)
    total_debit: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    total_credit: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    balanced: Mapped[bool] = mapped_column(Boolean, default=False)
    generated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    generated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    export_filename: Mapped[str | None] = mapped_column(String(255))

    period: Mapped[PayrollPeriod] = relationship(back_populates="journal_entries")
    lines: Mapped[list["JournalLine"]] = relationship(back_populates="entry", cascade="all, delete-orphan")


class JournalLine(Base):
    __tablename__ = "journal_lines"
    id: Mapped[int] = mapped_column(primary_key=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("journal_entries.id"))
    account: Mapped[str] = mapped_column(String(20))
    cost_center_code: Mapped[str | None] = mapped_column(String(20))
    concept: Mapped[PayrollConcept] = mapped_column(Enum(PayrollConcept))
    debit: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    credit: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    narrative: Mapped[str | None] = mapped_column(String(255))
    employee_code: Mapped[str | None] = mapped_column(String(40))

    entry: Mapped[JournalEntry] = relationship(back_populates="lines")


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(80))
    entity_type: Mapped[str | None] = mapped_column(String(60))
    entity_id: Mapped[int | None] = mapped_column()
    meta: Mapped[dict | None] = mapped_column(JSON)
    at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
