"""Siembra de datos de ejemplo + generación de Excel de muestra.

Ejecutar:  python -m app.seed
Crea la BD, maestros, usuarios y dos ficheros Excel de muestra en storage/.
"""
from __future__ import annotations

from openpyxl import Workbook

from .config import settings
from .database import SessionLocal, init_db
from .enums import (
    AccountingSide,
    DEFAULT_CONCEPT_ACCOUNT,
    DEFAULT_CONCEPT_SIDE,
    MappingScope,
    PayrollConcept,
    Role,
)
from .models import (
    AccountingMapping,
    Company,
    CostCenter,
    Department,
    Employee,
    User,
)
from .security import hash_password


def _reset(db):
    # Borrado idempotente para poder re-sembrar en demo
    for model in (AccountingMapping, Employee, Department, CostCenter, User, Company):
        db.query(model).delete()
    db.commit()


def seed():
    init_db()
    db = SessionLocal()
    try:
        _reset(db)

        # --- Sociedades ---
        norte = Company(code="SN", name="Automoción Norte S.L.", tax_id="B11111111", autoline_company_code="01")
        sur = Company(code="SS", name="Automoción Sur S.L.", tax_id="B22222222", autoline_company_code="02")
        db.add_all([norte, sur]); db.flush()

        # --- Centros de coste ---
        cc_vn = CostCenter(company_id=norte.id, code="VN", name="Ventas Vehículo Nuevo")
        cc_vo = CostCenter(company_id=norte.id, code="VO", name="Ventas Vehículo Ocasión")
        cc_pv = CostCenter(company_id=norte.id, code="PV", name="Postventa / Taller")
        db.add_all([cc_vn, cc_vo, cc_pv]); db.flush()

        # --- Departamentos ---
        d_ventas = Department(company_id=norte.id, name="Ventas", default_cost_center_id=cc_vn.id)
        d_postventa = Department(company_id=norte.id, name="Postventa", default_cost_center_id=cc_pv.id)
        db.add_all([d_ventas, d_postventa]); db.flush()

        # --- Empleados (maestro) ---
        e1 = Employee(employee_code="E001", full_name="Lucía Marín", national_id="11111111H",
                      email="lucia.marin@grupo.com", company_id=norte.id, department_id=d_ventas.id, cost_center_id=cc_vn.id)
        db.add(e1); db.flush()
        e2 = Employee(employee_code="E002", full_name="Diego Santos", national_id="22222222J",
                      email="diego.santos@grupo.com", company_id=norte.id, department_id=d_ventas.id,
                      cost_center_id=cc_vn.id, manager_id=e1.id)
        e3 = Employee(employee_code="E003", full_name="Marta Ruiz", national_id="33333333P",
                      email="marta.ruiz@grupo.com", company_id=norte.id, department_id=d_postventa.id, cost_center_id=cc_pv.id)
        db.add_all([e2, e3]); db.flush()

        # --- Mapeos contables a nivel DEPARTAMENTO (cuentas + centro de coste por concepto) ---
        for dept, cc in ((d_ventas, cc_vn), (d_postventa, cc_pv)):
            for concept in PayrollConcept:
                db.add(AccountingMapping(
                    scope=MappingScope.DEPARTMENT,
                    department_id=dept.id,
                    concept=concept,
                    account=DEFAULT_CONCEPT_ACCOUNT[concept],
                    # Las cuentas de pasivo (líquido, IRPF, SS organismos) no llevan centro de coste
                    cost_center_id=cc.id if DEFAULT_CONCEPT_SIDE[concept] == AccountingSide.DEBIT else None,
                    side=DEFAULT_CONCEPT_SIDE[concept],
                ))

        # --- Usuarios ---
        pwd = hash_password("demo1234")
        db.add_all([
            User(email="director@grupo.com", full_name="Dirección Sistemas", hashed_password=pwd, role=Role.ADMIN),
            User(email="jefe.ventas@grupo.com", full_name="Jefe de Ventas Norte", hashed_password=pwd,
                 role=Role.MANAGER, scope_company_id=norte.id, scope_department_id=d_ventas.id),
            User(email="rrhh@grupo.com", full_name="Recursos Humanos", hashed_password=pwd, role=Role.HR),
            User(email="conta@grupo.com", full_name="Contabilidad", hashed_password=pwd, role=Role.ACCOUNTING),
        ])
        db.commit()

        _make_sample_commissions()
        _make_sample_payroll()
        print("✔ Datos sembrados. BD:", settings.database_url)
        print("✔ Excel de muestra en:", settings.storage_dir)
        print("  Usuarios: director@grupo.com / jefe.ventas@grupo.com / rrhh@grupo.com / conta@grupo.com  (demo1234)")
    finally:
        db.close()


# Datos de muestra de nómina: (codigo, nombre, fijo, variable, ss_empresa, ss_trab, irpf)
_PAYROLL = [
    ("E001", "Lucía Marín", 2000.0, 800.0),
    ("E002", "Diego Santos", 1500.0, 1200.0),
    ("E003", "Marta Ruiz", 1800.0, 300.0),
]


def _make_sample_commissions():
    wb = Workbook(); ws = wb.active; ws.title = "Comisiones"
    ws.append(["codigo_empleado", "nombre", "departamento", "concepto", "importe", "observaciones"])
    ws.append(["E001", "Lucía Marín", "Ventas", "Comisión VN", 800.00, "5 vehículos"])
    ws.append(["E002", "Diego Santos", "Ventas", "Comisión VN", 1200.00, "8 vehículos"])
    ws.append(["E003", "Marta Ruiz", "Postventa", "Objetivo taller", 300.00, "Cumplimiento"])
    path = settings.storage_dir / "ejemplo_comisiones.xlsx"
    wb.save(path)


def _make_sample_payroll():
    """Genera el Excel resumen que devolvería la gestoría, con cuadre coherente."""
    wb = Workbook(); ws = wb.active; ws.title = "Nominas"
    ws.append(["codigo_empleado", "nombre", "salario_fijo", "salario_variable",
               "ss_empresa", "ss_trabajador", "irpf", "liquido"])
    for code, name, fijo, variable in _PAYROLL:
        bruto = fijo + variable
        ss_emp = round(bruto * 0.30, 2)
        ss_trab = round(bruto * 0.0635, 2)
        irpf = round(bruto * 0.13, 2)
        liquido = round(bruto - ss_trab - irpf, 2)  # garantiza el cuadre del asiento
        ws.append([code, name, fijo, variable, ss_emp, ss_trab, irpf, liquido])
    path = settings.storage_dir / "ejemplo_nominas_gestoria.xlsx"
    wb.save(path)


if __name__ == "__main__":
    seed()
