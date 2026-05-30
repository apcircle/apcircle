"""Esquemas Pydantic para la API."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from .enums import (
    ApprovalDecision,
    ApprovalLevel,
    PayrollConcept,
    PeriodStatus,
    Role,
    ValidationStatus,
)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Auth ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Role
    full_name: str


class UserOut(ORMModel):
    id: int
    email: EmailStr
    full_name: str
    role: Role
    scope_company_id: int | None = None
    scope_department_id: int | None = None


# --- Maestros ---
class CompanyOut(ORMModel):
    id: int
    code: str
    name: str
    autoline_company_code: str


class EmployeeOut(ORMModel):
    id: int
    employee_code: str
    full_name: str
    national_id: str | None = None
    company_id: int
    department_id: int | None = None
    cost_center_id: int | None = None
    manager_id: int | None = None
    active: bool


class EmployeeCreate(BaseModel):
    employee_code: str
    full_name: str
    national_id: str | None = None
    email: EmailStr | None = None
    company_id: int
    department_id: int | None = None
    cost_center_id: int | None = None
    manager_id: int | None = None


# --- Periodos ---
class PeriodCreate(BaseModel):
    code: str
    company_id: int | None = None


class PeriodOut(ORMModel):
    id: int
    code: str
    company_id: int | None = None
    status: PeriodStatus
    created_at: datetime


class TransitionOut(ORMModel):
    from_status: PeriodStatus
    to_status: PeriodStatus
    at: datetime
    note: str | None = None


# --- Importaciones ---
class CommissionLineOut(ORMModel):
    id: int
    employee_code: str
    employee_id: int | None = None
    department: str | None = None
    concept: str
    amount: float
    validation_status: ValidationStatus


class PayrollLineOut(ORMModel):
    id: int
    employee_code: str
    employee_id: int | None = None
    concept: PayrollConcept
    amount: float
    validation_status: ValidationStatus
    validation_message: str | None = None


class ImportResult(BaseModel):
    import_id: int
    row_count: int
    unmatched: int = 0
    errors: list[str] = []


# --- Validación de nóminas ---
class ValidationReport(BaseModel):
    ok: bool
    total_lines: int
    unmatched_employees: list[str] = []
    missing_mappings: list[str] = []
    issues: list[str] = []


# --- Aprobaciones ---
class ApprovalIn(BaseModel):
    decision: ApprovalDecision
    comment: str | None = None
    level: ApprovalLevel | None = None  # se infiere del rol si no se indica


# --- Asiento ---
class JournalLineOut(ORMModel):
    account: str
    cost_center_code: str | None = None
    concept: PayrollConcept
    debit: float
    credit: float
    narrative: str | None = None
    employee_code: str | None = None


class JournalEntryOut(ORMModel):
    id: int
    period_id: int
    entry_date: date
    total_debit: float
    total_credit: float
    balanced: bool
    export_filename: str | None = None
    lines: list[JournalLineOut] = []
