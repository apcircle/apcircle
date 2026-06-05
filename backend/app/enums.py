"""Enumeraciones del dominio."""
from __future__ import annotations

import enum


class Role(str, enum.Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    HR = "HR"
    ACCOUNTING = "ACCOUNTING"
    VIEWER = "VIEWER"


class PeriodStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    COMMISSIONS_IMPORTED = "COMMISSIONS_IMPORTED"
    PENDING_MANAGER_APPROVAL = "PENDING_MANAGER_APPROVAL"
    MANAGER_APPROVED = "MANAGER_APPROVED"
    HR_APPROVED = "HR_APPROVED"
    SENT_TO_GESTORIA = "SENT_TO_GESTORIA"
    PAYROLL_RECEIVED = "PAYROLL_RECEIVED"
    PAYROLL_VALIDATED = "PAYROLL_VALIDATED"
    JOURNAL_GENERATED = "JOURNAL_GENERATED"
    CLOSED = "CLOSED"


class PayrollConcept(str, enum.Enum):
    SALARIO_FIJO = "SALARIO_FIJO"
    SALARIO_VARIABLE = "SALARIO_VARIABLE"
    SEGURIDAD_SOCIAL_EMPRESA = "SEGURIDAD_SOCIAL_EMPRESA"
    SEGURIDAD_SOCIAL_TRABAJADOR = "SEGURIDAD_SOCIAL_TRABAJADOR"
    RETENCION_IRPF = "RETENCION_IRPF"
    LIQUIDO_A_PAGAR = "LIQUIDO_A_PAGAR"
    ANTICIPOS = "ANTICIPOS"


class AccountingSide(str, enum.Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class MappingScope(str, enum.Enum):
    EMPLOYEE = "EMPLOYEE"
    DEPARTMENT = "DEPARTMENT"


class ValidationStatus(str, enum.Enum):
    PENDING = "PENDING"
    OK = "OK"
    UNMATCHED = "UNMATCHED"        # empleado no encontrado en el maestro
    NO_MAPPING = "NO_MAPPING"      # falta cuenta/centro de coste configurado
    ERROR = "ERROR"               # importe u otro dato incorrecto


class ApprovalLevel(str, enum.Enum):
    MANAGER = "MANAGER"
    HR = "HR"


class ApprovalDecision(str, enum.Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# Naturaleza contable por defecto de cada concepto (lado del asiento).
# Es el valor por defecto al sembrar mapeos; el AccountingMapping puede sobreescribirlo.
DEFAULT_CONCEPT_SIDE: dict[PayrollConcept, AccountingSide] = {
    PayrollConcept.SALARIO_FIJO: AccountingSide.DEBIT,
    PayrollConcept.SALARIO_VARIABLE: AccountingSide.DEBIT,
    PayrollConcept.SEGURIDAD_SOCIAL_EMPRESA: AccountingSide.DEBIT,
    PayrollConcept.SEGURIDAD_SOCIAL_TRABAJADOR: AccountingSide.CREDIT,
    PayrollConcept.RETENCION_IRPF: AccountingSide.CREDIT,
    PayrollConcept.LIQUIDO_A_PAGAR: AccountingSide.CREDIT,
    PayrollConcept.ANTICIPOS: AccountingSide.CREDIT,
}

# Cuentas contables por defecto (PGC España, configurables por mapeo).
DEFAULT_CONCEPT_ACCOUNT: dict[PayrollConcept, str] = {
    PayrollConcept.SALARIO_FIJO: "640000",
    PayrollConcept.SALARIO_VARIABLE: "640001",
    PayrollConcept.SEGURIDAD_SOCIAL_EMPRESA: "642000",
    PayrollConcept.SEGURIDAD_SOCIAL_TRABAJADOR: "476000",
    PayrollConcept.RETENCION_IRPF: "475100",
    PayrollConcept.LIQUIDO_A_PAGAR: "465000",
    PayrollConcept.ANTICIPOS: "460000",
}
