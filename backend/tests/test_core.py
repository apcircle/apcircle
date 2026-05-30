"""Tests del núcleo de valor: parseo de Excel, validación y cuadre del asiento."""
from __future__ import annotations

from openpyxl import Workbook

from app.enums import PayrollConcept, PeriodStatus, ValidationStatus
from app.models import PayrollPeriod
from app.services import autoline_export, excel_commissions, excel_payroll, validation


def _write(tmp_path, name, headers, rows):
    wb = Workbook(); ws = wb.active
    ws.append(headers)
    for r in rows:
        ws.append(r)
    path = tmp_path / name
    wb.save(path)
    return str(path)


def _period(db, master):
    p = PayrollPeriod(code="2026-05", company_id=master["company"].id, status=PeriodStatus.SENT_TO_GESTORIA)
    db.add(p); db.commit()
    return p


def test_parse_commissions_tolerant_headers(tmp_path):
    path = _write(tmp_path, "com.xlsx",
                  ["Código Empleado", "Nombre", "Departamento", "Concepto", "Importe"],
                  [["E001", "Lucía", "Ventas", "Comisión", "1.234,56"]])
    rows = excel_commissions.parse_workbook(path)
    assert len(rows) == 1
    assert rows[0]["employee_code"] == "E001"
    assert rows[0]["amount"] == 1234.56  # acepta formato español


def test_commission_unmatched_employee(db, master, tmp_path):
    path = _write(tmp_path, "com.xlsx",
                  ["codigo_empleado", "importe"],
                  [["E001", 800], ["E999", 100]])
    period = _period(db, master)
    imp = excel_commissions.ingest(db, period_id=period.id, filename="com.xlsx", stored_path=path, uploaded_by=None)
    db.commit()
    statuses = {l.employee_code: l.validation_status for l in imp.lines}
    assert statuses["E001"] == ValidationStatus.OK
    assert statuses["E999"] == ValidationStatus.UNMATCHED


def test_payroll_validation_detects_missing_employee(db, master, tmp_path):
    path = _write(tmp_path, "nom.xlsx",
                  ["codigo_empleado", "salario_fijo", "salario_variable", "ss_empresa", "ss_trabajador", "irpf", "liquido"],
                  [["E001", 2000, 800, 840, 177.80, 364, 2258.20],
                   ["E777", 1000, 0, 300, 63.50, 130, 806.50]])
    period = _period(db, master)
    imp = excel_payroll.ingest(db, period_id=period.id, filename="nom.xlsx", stored_path=path, uploaded_by=None)
    db.commit()
    report = validation.validate_payroll_import(db, imp)
    assert not report.ok
    assert "E777" in report.unmatched_employees


def test_journal_is_balanced(db, master, tmp_path):
    fijo, variable = 2000.0, 800.0
    bruto = fijo + variable
    ss_emp = round(bruto * 0.30, 2)
    ss_trab = round(bruto * 0.0635, 2)
    irpf = round(bruto * 0.13, 2)
    liquido = round(bruto - ss_trab - irpf, 2)
    path = _write(tmp_path, "nom.xlsx",
                  ["codigo_empleado", "salario_fijo", "salario_variable", "ss_empresa", "ss_trabajador", "irpf", "liquido"],
                  [["E001", fijo, variable, ss_emp, ss_trab, irpf, liquido]])
    period = _period(db, master)
    imp = excel_payroll.ingest(db, period_id=period.id, filename="nom.xlsx", stored_path=path, uploaded_by=None)
    db.commit()

    report = validation.validate_payroll_import(db, imp)
    assert report.ok, report

    entry = autoline_export.build_journal(db, period, imp)
    db.commit()

    assert entry.balanced is True
    assert entry.total_debit == entry.total_credit
    # DEBE = fijo + variable + ss_empresa
    assert float(entry.total_debit) == round(fijo + variable + ss_emp, 2)


def test_journal_separates_fixed_variable_and_ss(db, master, tmp_path):
    path = _write(tmp_path, "nom.xlsx",
                  ["codigo_empleado", "salario_fijo", "salario_variable", "ss_empresa", "ss_trabajador", "irpf", "liquido"],
                  [["E001", 2000, 800, 840, 177.80, 364, 2258.20]])
    period = _period(db, master)
    imp = excel_payroll.ingest(db, period_id=period.id, filename="nom.xlsx", stored_path=path, uploaded_by=None)
    db.commit()
    validation.validate_payroll_import(db, imp)
    entry = autoline_export.build_journal(db, period, imp)
    db.commit()

    by_concept = {l.concept: l for l in entry.lines}
    assert PayrollConcept.SALARIO_FIJO in by_concept
    assert PayrollConcept.SALARIO_VARIABLE in by_concept
    assert PayrollConcept.SEGURIDAD_SOCIAL_EMPRESA in by_concept
    # Cuentas separadas por concepto
    assert by_concept[PayrollConcept.SALARIO_FIJO].account != by_concept[PayrollConcept.SALARIO_VARIABLE].account
    # El salario fijo va al debe con centro de coste
    assert float(by_concept[PayrollConcept.SALARIO_FIJO].debit) == 2000
    assert by_concept[PayrollConcept.SALARIO_FIJO].cost_center_code == "VN"
