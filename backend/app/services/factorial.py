"""Conector Factorial (opcional). Adapter con modo 'stub' (simulado) o 'live' (API real).

El maestro de empleados es la fuente de verdad contable; Factorial aporta la jerarquía y
las altas/bajas. La sincronización:
  - hace upsert por factorial_id (respaldo por employee_code),
  - resuelve la relación manager (jerarquía de aprobación),
  - da de baja (active=False) a quien ya no aparece o está terminado en Factorial,
  - NUNCA sobrescribe las cuentas contables (AccountingMapping) configuradas a mano.

Modo 'live': cliente HTTP real con paginación y autenticación configurable
(API key vía header x-api-key, o Bearer). El endpoint es parametrizable porque la
versión de la API de Factorial cambia con el tiempo (ver config.factorial_employees_path).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import httpx
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Department, Employee


@dataclass
class SyncReport:
    created: int = 0
    updated: int = 0
    deactivated: int = 0
    managers_linked: int = 0
    pending_mapping: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


# --- Normalización: ambos modos devuelven este esquema homogéneo ---
# {factorial_id, code, full_name, email, manager_factorial_id, active, team_name}


def _normalize(raw: dict) -> dict:
    """Adapta un registro de empleado de Factorial al esquema interno, de forma defensiva."""
    fid = str(raw.get("id") or raw.get("employee_id") or "")
    first = raw.get("first_name") or raw.get("firstName") or ""
    last = raw.get("last_name") or raw.get("lastName") or ""
    full_name = (raw.get("full_name") or f"{first} {last}").strip()
    manager = raw.get("manager_id") or raw.get("reports_to_id") or raw.get("manager_factorial_id")
    # Factorial marca la baja con una fecha de terminación; si existe y ya pasó => inactivo.
    terminated = raw.get("terminated_on") or raw.get("termination_date")
    active = raw.get("active")
    if active is None:
        active = terminated in (None, "", False)
    return {
        "factorial_id": fid,
        "code": raw.get("code") or raw.get("identifier") or raw.get("employee_code"),
        "full_name": full_name,
        "email": raw.get("email") or raw.get("login_email"),
        "manager_factorial_id": str(manager) if manager else None,
        "active": bool(active),
        "team_name": raw.get("team_name") or raw.get("team"),
    }


def _stub_employees() -> list[dict]:
    return [
        _normalize({"id": "F-1001", "first_name": "Lucía", "last_name": "Marín",
                    "email": "lucia.marin@grupo.com", "code": "E001", "team": "Ventas", "active": True}),
        _normalize({"id": "F-1002", "first_name": "Diego", "last_name": "Santos",
                    "email": "diego.santos@grupo.com", "code": "E002", "manager_id": "F-1001",
                    "team": "Ventas", "active": True}),
        _normalize({"id": "F-1003", "first_name": "Marta", "last_name": "Ruiz",
                    "email": "marta.ruiz@grupo.com", "code": "E003", "team": "Postventa", "active": True}),
    ]


def _live_headers() -> dict[str, str]:
    key = settings.factorial_api_key or ""
    if settings.factorial_auth_scheme == "bearer":
        return {"Authorization": f"Bearer {key}", "Accept": "application/json"}
    return {"x-api-key": key, "Accept": "application/json"}


def _fetch_employees() -> list[dict]:
    """Obtiene los empleados desde Factorial (paginado) y los normaliza."""
    if settings.factorial_mode != "live":
        return _stub_employees()
    if not settings.factorial_api_key:
        raise RuntimeError("FACTORIAL_MODE=live requiere FACTORIAL_API_KEY configurada")

    results: list[dict] = []
    page = 1
    with httpx.Client(base_url=settings.factorial_base_url, headers=_live_headers(), timeout=30) as client:
        while True:
            resp = client.get(
                settings.factorial_employees_path,
                params={"page": page, "per_page": settings.factorial_page_size},
            )
            resp.raise_for_status()
            payload = resp.json()
            # Factorial puede devolver una lista plana o {"data": [...], "meta": {...}}
            batch = payload.get("data", payload) if isinstance(payload, dict) else payload
            if not batch:
                break
            results.extend(_normalize(r) for r in batch)
            # corta cuando la página no llena el tamaño solicitado
            if len(batch) < settings.factorial_page_size:
                break
            page += 1
    return results


def sync_employees(db: Session, *, default_company_id: int) -> SyncReport:
    """Sincroniza el maestro desde Factorial. Idempotente."""
    report = SyncReport()
    try:
        rows = _fetch_employees()
    except (httpx.HTTPError, RuntimeError) as exc:
        report.errors.append(f"Error al conectar con Factorial: {exc}")
        return report

    existing_by_fid = {e.factorial_id: e for e in db.query(Employee).filter(Employee.factorial_id.isnot(None)).all()}
    by_code = {e.employee_code: e for e in db.query(Employee).all()}
    departments = {d.name.strip().lower(): d for d in db.query(Department).all()}

    seen_fids: set[str] = set()
    # factorial_id -> Employee, para enlazar managers en una segunda pasada
    fid_to_emp: dict[str, Employee] = {}
    pending_manager: list[tuple[Employee, str]] = []

    for row in rows:
        fid = row["factorial_id"]
        if not fid:
            report.errors.append(f"Registro sin id de Factorial: {row.get('full_name')}")
            continue
        seen_fids.add(fid)

        emp = existing_by_fid.get(fid) or (by_code.get(row["code"]) if row["code"] else None)
        is_new = emp is None
        if is_new:
            emp = Employee(
                factorial_id=fid,
                employee_code=row["code"] or fid,
                full_name=row["full_name"],
                email=row["email"],
                company_id=default_company_id,
                active=row["active"],
            )
            db.add(emp)
            db.flush()
            report.created += 1
        else:
            emp.factorial_id = fid
            emp.full_name = row["full_name"] or emp.full_name
            emp.email = row["email"] or emp.email
            emp.active = row["active"]
            report.updated += 1

        # Mapeo opcional team -> Department (sin tocar centro de coste / cuentas)
        if settings.factorial_map_team_to_department and row["team_name"]:
            dept = departments.get(row["team_name"].strip().lower())
            if dept and emp.department_id is None:
                emp.department_id = dept.id

        fid_to_emp[fid] = emp
        if row["manager_factorial_id"]:
            pending_manager.append((emp, row["manager_factorial_id"]))

        # "Pendiente de configurar" = creado sin departamento (sin cuentas contables resolubles)
        if is_new and emp.department_id is None:
            report.pending_mapping.append(emp.employee_code)

    # Segunda pasada: enlazar la jerarquía de managers
    for emp, manager_fid in pending_manager:
        manager = fid_to_emp.get(manager_fid) or existing_by_fid.get(manager_fid)
        if manager and emp.manager_id != manager.id:
            emp.manager_id = manager.id
            report.managers_linked += 1

    # Bajas: empleados con factorial_id que ya no aparecen en Factorial
    for fid, emp in existing_by_fid.items():
        if fid not in seen_fids and emp.active:
            emp.active = False
            report.deactivated += 1

    return report
