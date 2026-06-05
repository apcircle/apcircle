"""Validación de las líneas de nómina contra el maestro de empleados y mapeos contables."""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..enums import ValidationStatus
from ..models import Employee, PayrollImport, PayrollLine
from ..schemas import ValidationReport
from . import mapping


def validate_payroll_import(db: Session, imp: PayrollImport) -> ValidationReport:
    """Valida cada línea: empleado existe en maestro + tiene mapeo contable + importe válido.

    Actualiza el estado de validación de cada línea y devuelve un informe consolidado.
    """
    employees = {e.employee_code: e for e in db.query(Employee).all()}
    unmatched: set[str] = set()
    missing_mappings: set[str] = set()
    issues: list[str] = []

    lines = db.query(PayrollLine).filter(PayrollLine.import_id == imp.id).all()
    for line in lines:
        emp: Employee | None = employees.get(line.employee_code)
        if emp is None:
            line.validation_status = ValidationStatus.UNMATCHED
            line.validation_message = "Empleado no encontrado en el maestro"
            unmatched.add(line.employee_code)
            continue

        line.employee_id = emp.id

        if not emp.active:
            issues.append(f"{line.employee_code}: empleado dado de baja en el maestro")

        if line.amount is None or float(line.amount) < 0:
            line.validation_status = ValidationStatus.ERROR
            line.validation_message = "Importe inválido"
            issues.append(f"{line.employee_code}/{line.concept.value}: importe inválido")
            continue

        resolved = mapping.resolve(db, emp, line.concept)
        if resolved is None:
            line.validation_status = ValidationStatus.NO_MAPPING
            line.validation_message = f"Sin cuenta configurada para {line.concept.value}"
            missing_mappings.add(f"{line.employee_code} · {line.concept.value}")
            continue

        line.validation_status = ValidationStatus.OK
        line.validation_message = None

    ok = not unmatched and not missing_mappings and not issues
    return ValidationReport(
        ok=ok,
        total_lines=len(lines),
        unmatched_employees=sorted(unmatched),
        missing_mappings=sorted(missing_mappings),
        issues=issues,
    )
