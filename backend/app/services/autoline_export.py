"""Construcción del asiento de nóminas y exportación al formato de importación de Autoline.

Modelo contable (PGC España, cuadre garantizado):

    DEBE                                   HABER
    640 Sueldos y salarios (fijo)          465 Remun. pendientes de pago (líquido)
    640 Retrib. variable (comisiones)      475 HP acreedora retenciones (IRPF)
    642 SS a cargo empresa                 476 Organismos SS (SS trab. + SS empresa)

Las cuentas y centros de coste son configurables vía AccountingMapping; la semántica
contable (qué va al debe y qué al haber, y el doble apunte de la SS empresa) es fija.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook
from sqlalchemy.orm import Session

from ..config import settings
from ..enums import PayrollConcept, ValidationStatus
from ..models import (
    Employee,
    JournalEntry,
    JournalLine,
    PayrollImport,
    PayrollLine,
    PayrollPeriod,
)
from . import audit, mapping

# Columnas por defecto del fichero de importación de Autoline (Nominal Journal Import).
AUTOLINE_COLUMNS = [
    "Company",
    "Account",
    "CostCentre",
    "Period",
    "Date",
    "Debit",
    "Credit",
    "Narrative",
    "Reference",
]

CONCEPT_LABEL = {
    PayrollConcept.SALARIO_FIJO: "Salario fijo",
    PayrollConcept.SALARIO_VARIABLE: "Salario variable",
    PayrollConcept.SEGURIDAD_SOCIAL_EMPRESA: "SS empresa",
    PayrollConcept.SEGURIDAD_SOCIAL_TRABAJADOR: "SS trabajador",
    PayrollConcept.RETENCION_IRPF: "Retención IRPF",
    PayrollConcept.LIQUIDO_A_PAGAR: "Líquido a pagar",
    PayrollConcept.ANTICIPOS: "Anticipos",
}


def _q(value: float) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


class _Builder:
    """Acumula apuntes (cuenta, centro de coste, concepto, debe, haber)."""

    def __init__(self, period_code: str):
        self.period_code = period_code
        self.rows: list[dict] = []

    def add(self, *, account: str, cc: str | None, concept: PayrollConcept, debit=0, credit=0, employee_code: str):
        self.rows.append(
            {
                "account": account,
                "cost_center_code": cc,
                "concept": concept,
                "debit": _q(debit),
                "credit": _q(credit),
                "narrative": f"Nómina {self.period_code} · {CONCEPT_LABEL[concept]}",
                "employee_code": employee_code,
            }
        )


def _aggregate_by_employee(db: Session, imp: PayrollImport) -> dict[int, dict[PayrollConcept, float]]:
    data: dict[int, dict[PayrollConcept, float]] = defaultdict(lambda: defaultdict(float))
    lines = (
        db.query(PayrollLine)
        .filter(PayrollLine.import_id == imp.id, PayrollLine.validation_status == ValidationStatus.OK)
        .all()
    )
    for ln in lines:
        if ln.employee_id is None:
            continue
        data[ln.employee_id][ln.concept] += float(ln.amount)
    return data


def build_journal(db: Session, period: PayrollPeriod, imp: PayrollImport) -> JournalEntry:
    """Genera el JournalEntry + líneas a partir de la importación de nóminas validada."""
    builder = _Builder(period.code)
    by_employee = _aggregate_by_employee(db, imp)

    for employee_id, concepts in by_employee.items():
        emp: Employee = db.get(Employee, employee_id)
        code = emp.employee_code

        def acc(concept: PayrollConcept):
            m = mapping.resolve(db, emp, concept)
            # validación previa garantiza que existe; guarda por robustez
            return (m.account, m.cost_center_code) if m else (None, None)

        # --- DEBE (gastos) ---
        if concepts.get(PayrollConcept.SALARIO_FIJO):
            a, cc = acc(PayrollConcept.SALARIO_FIJO)
            builder.add(account=a, cc=cc, concept=PayrollConcept.SALARIO_FIJO,
                        debit=concepts[PayrollConcept.SALARIO_FIJO], employee_code=code)
        if concepts.get(PayrollConcept.SALARIO_VARIABLE):
            a, cc = acc(PayrollConcept.SALARIO_VARIABLE)
            builder.add(account=a, cc=cc, concept=PayrollConcept.SALARIO_VARIABLE,
                        debit=concepts[PayrollConcept.SALARIO_VARIABLE], employee_code=code)

        ss_empresa = concepts.get(PayrollConcept.SEGURIDAD_SOCIAL_EMPRESA, 0.0)
        if ss_empresa:
            a, cc = acc(PayrollConcept.SEGURIDAD_SOCIAL_EMPRESA)
            builder.add(account=a, cc=cc, concept=PayrollConcept.SEGURIDAD_SOCIAL_EMPRESA,
                        debit=ss_empresa, employee_code=code)

        # --- HABER (deudas) ---
        if concepts.get(PayrollConcept.RETENCION_IRPF):
            a, cc = acc(PayrollConcept.RETENCION_IRPF)
            builder.add(account=a, cc=cc, concept=PayrollConcept.RETENCION_IRPF,
                        credit=concepts[PayrollConcept.RETENCION_IRPF], employee_code=code)
        if concepts.get(PayrollConcept.LIQUIDO_A_PAGAR):
            a, cc = acc(PayrollConcept.LIQUIDO_A_PAGAR)
            builder.add(account=a, cc=cc, concept=PayrollConcept.LIQUIDO_A_PAGAR,
                        credit=concepts[PayrollConcept.LIQUIDO_A_PAGAR], employee_code=code)

        # Organismos SS (476): SS trabajador + SS empresa (doble apunte de la SS empresa)
        ss_trab = concepts.get(PayrollConcept.SEGURIDAD_SOCIAL_TRABAJADOR, 0.0)
        ss_org_total = ss_trab + ss_empresa
        if ss_org_total:
            a, cc = acc(PayrollConcept.SEGURIDAD_SOCIAL_TRABAJADOR)
            builder.add(account=a, cc=cc, concept=PayrollConcept.SEGURIDAD_SOCIAL_TRABAJADOR,
                        credit=ss_org_total, employee_code=code)

    # Nivel de detalle: agrupado (summary) o por empleado
    rows = builder.rows
    if settings.autoline_detail_level == "summary":
        rows = _summarize(rows)

    total_debit = sum(r["debit"] for r in rows)
    total_credit = sum(r["credit"] for r in rows)

    entry = JournalEntry(
        period_id=period.id,
        company_id=period.company_id,
        entry_date=date.today(),
        total_debit=total_debit,
        total_credit=total_credit,
        balanced=(total_debit == total_credit),
    )
    db.add(entry)
    db.flush()

    for r in rows:
        db.add(
            JournalLine(
                entry_id=entry.id,
                account=r["account"],
                cost_center_code=r["cost_center_code"],
                concept=r["concept"],
                debit=r["debit"],
                credit=r["credit"],
                narrative=r["narrative"],
                employee_code=r["employee_code"],
            )
        )
    audit.record(db, actor_id=entry.generated_by, action="journal.generate",
                 entity_type="JournalEntry", entity_id=entry.id,
                 meta={"balanced": entry.balanced, "debit": str(total_debit), "credit": str(total_credit)})
    return entry


def _summarize(rows: list[dict]) -> list[dict]:
    """Agrupa por (cuenta, centro de coste, concepto) sumando debe y haber."""
    grouped: dict[tuple, dict] = {}
    for r in rows:
        key = (r["account"], r["cost_center_code"], r["concept"])
        if key not in grouped:
            grouped[key] = {**r, "employee_code": None}
        else:
            grouped[key]["debit"] += r["debit"]
            grouped[key]["credit"] += r["credit"]
    return list(grouped.values())


def export_xlsx(db: Session, period: PayrollPeriod, entry: JournalEntry) -> Path:
    """Genera el .xlsx de importación de Autoline y devuelve la ruta."""
    company = period.company
    company_code = company.autoline_company_code if company else settings.autoline_default_company_code

    wb = Workbook()
    ws = wb.active
    ws.title = "Asiento Nominas"
    ws.append(AUTOLINE_COLUMNS)

    reference = f"NOM-{period.code}"
    # La sesión usa autoflush=False; forzamos el flush para que las líneas recién
    # creadas en build_journal sean visibles en esta consulta.
    db.flush()
    lines = db.query(JournalLine).filter(JournalLine.entry_id == entry.id).all()
    for ln in lines:
        ws.append([
            company_code,
            ln.account,
            ln.cost_center_code or "",
            period.code,
            entry.entry_date.isoformat(),
            float(ln.debit) if ln.debit else None,
            float(ln.credit) if ln.credit else None,
            ln.narrative,
            reference,
        ])
    # Fila de totales (informativa, comentada para no romper importadores estrictos)
    ws.append([])
    ws.append(["", "", "", "", "TOTALES", float(entry.total_debit), float(entry.total_credit), "", ""])

    filename = f"asiento_autoline_{period.code}.xlsx"
    path = settings.storage_dir / filename
    wb.save(path)
    entry.export_filename = filename
    return path
