"""Conector Factorial (opcional). Adapter con modo 'stub' (simulado) o 'live' (API real).

El maestro de empleados es la fuente de verdad contable; Factorial aporta jerarquía y
altas/bajas. La sincronización NUNCA sobrescribe las cuentas contables configuradas a mano.
"""
from __future__ import annotations

from dataclasses import dataclass

import httpx
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Employee


@dataclass
class SyncReport:
    created: int = 0
    updated: int = 0
    deactivated: int = 0
    pending_mapping: list[str] = None  # type: ignore

    def __post_init__(self):
        if self.pending_mapping is None:
            self.pending_mapping = []


def _fetch_employees() -> list[dict]:
    """Devuelve empleados desde Factorial. En modo stub, datos simulados."""
    if settings.factorial_mode != "live":
        return [
            {"id": "F-1001", "first_name": "Lucía", "last_name": "Marín", "email": "lucia.marin@grupo.com",
             "code": "E001", "manager_code": None, "active": True},
            {"id": "F-1002", "first_name": "Diego", "last_name": "Santos", "email": "diego.santos@grupo.com",
             "code": "E002", "manager_code": "E001", "active": True},
        ]
    headers = {"Authorization": f"Bearer {settings.factorial_api_key}"}
    with httpx.Client(base_url=settings.factorial_base_url, headers=headers, timeout=30) as client:
        resp = client.get("/employees")
        resp.raise_for_status()
        return resp.json()


def sync_employees(db: Session, *, default_company_id: int) -> SyncReport:
    """Upsert de empleados desde Factorial por factorial_id. No toca datos contables."""
    report = SyncReport()
    existing = {e.factorial_id: e for e in db.query(Employee).filter(Employee.factorial_id.isnot(None)).all()}
    by_code = {e.employee_code: e for e in db.query(Employee).all()}

    for row in _fetch_employees():
        fid = str(row["id"])
        full_name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
        emp = existing.get(fid) or by_code.get(row.get("code", ""))
        if emp is None:
            emp = Employee(
                factorial_id=fid,
                employee_code=row.get("code") or fid,
                full_name=full_name,
                email=row.get("email"),
                company_id=default_company_id,
                active=row.get("active", True),
            )
            db.add(emp)
            db.flush()
            report.created += 1
            # sin cuentas contables configuradas todavía
            report.pending_mapping.append(emp.employee_code)
        else:
            emp.factorial_id = fid
            emp.full_name = full_name or emp.full_name
            emp.email = row.get("email") or emp.email
            emp.active = row.get("active", emp.active)
            report.updated += 1

    return report
