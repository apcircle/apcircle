"""Ciclo de vida del periodo de nómina: ingesta, aprobaciones, gestoría, asiento."""
from __future__ import annotations

import shutil
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..enums import ApprovalDecision, ApprovalLevel, PeriodStatus, Role, ValidationStatus
from ..models import (
    Approval,
    CommissionImport,
    JournalEntry,
    PayrollImport,
    PayrollLine,
    PayrollPeriod,
    User,
)
from ..schemas import (
    ApprovalIn,
    ImportResult,
    JournalEntryOut,
    PeriodCreate,
    PeriodOut,
    TransitionOut,
    ValidationReport,
)
from ..security import get_current_user, require_roles
from ..services import autoline_export, email, excel_commissions, excel_payroll, validation, workflow

router = APIRouter(prefix="/api/periods", tags=["periodos"])


def _save_upload(file: UploadFile, prefix: str) -> str:
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    safe = file.filename.replace("/", "_")
    dest = settings.storage_dir / f"{prefix}_{ts}_{safe}"
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    return str(dest)


def _get_period(db: Session, period_id: int) -> PayrollPeriod:
    period = db.get(PayrollPeriod, period_id)
    if not period:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Periodo no encontrado")
    return period


@router.post("", response_model=PeriodOut, status_code=201)
def create_period(
    payload: PeriodCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.MANAGER, Role.HR)),
):
    if db.query(PayrollPeriod).filter(PayrollPeriod.code == payload.code).first():
        raise HTTPException(status.HTTP_409_CONFLICT, f"Ya existe el periodo {payload.code}")
    period = PayrollPeriod(code=payload.code, company_id=payload.company_id, created_by=user.id)
    db.add(period)
    db.commit()
    db.refresh(period)
    return period


@router.get("", response_model=list[PeriodOut])
def list_periods(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(PayrollPeriod).order_by(PayrollPeriod.code.desc()).all()


@router.get("/{period_id}", response_model=PeriodOut)
def get_period(period_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return _get_period(db, period_id)


@router.get("/{period_id}/transitions", response_model=list[TransitionOut])
def get_transitions(period_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    period = _get_period(db, period_id)
    return sorted(period.transitions, key=lambda t: t.at)


# --- 1. Ingesta de comisiones ---
@router.post("/{period_id}/commissions", response_model=ImportResult)
def upload_commissions(
    period_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.MANAGER, Role.HR)),
):
    period = _get_period(db, period_id)
    if period.status not in (PeriodStatus.DRAFT, PeriodStatus.COMMISSIONS_IMPORTED):
        raise HTTPException(status.HTTP_409_CONFLICT, "El periodo no admite carga de comisiones en su estado actual")
    path = _save_upload(file, f"comisiones_{period.code}")
    try:
        imp = excel_commissions.ingest(db, period_id=period.id, filename=file.filename, stored_path=path, uploaded_by=user.id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))

    unmatched = sum(1 for l in imp.lines if l.validation_status == ValidationStatus.UNMATCHED)
    if period.status == PeriodStatus.DRAFT:
        workflow.transition(db, period, PeriodStatus.COMMISSIONS_IMPORTED, actor_id=user.id, note=f"Carga {file.filename}")
    db.commit()
    errors = [f"Empleado no encontrado: {l.employee_code}" for l in imp.lines if l.validation_status == ValidationStatus.UNMATCHED]
    return ImportResult(import_id=imp.id, row_count=imp.row_count, unmatched=unmatched, errors=errors[:20])


@router.post("/{period_id}/submit-approval", response_model=PeriodOut)
def submit_for_approval(
    period_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.MANAGER, Role.HR)),
):
    period = _get_period(db, period_id)
    workflow.transition(db, period, PeriodStatus.PENDING_MANAGER_APPROVAL, actor_id=user.id, note="Enviado a aprobación")
    db.commit()
    db.refresh(period)
    return period


# --- 2 y 3. Aprobaciones (responsable / RRHH) ---
@router.post("/{period_id}/approve", response_model=PeriodOut)
def approve(
    period_id: int,
    payload: ApprovalIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    period = _get_period(db, period_id)
    level = payload.level or (ApprovalLevel.HR if user.role in (Role.HR, Role.ADMIN) else ApprovalLevel.MANAGER)

    # Validación de rol según nivel y estado
    if level == ApprovalLevel.MANAGER:
        if user.role not in (Role.MANAGER, Role.ADMIN):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo responsables pueden aprobar a nivel MANAGER")
        if period.status != PeriodStatus.PENDING_MANAGER_APPROVAL:
            raise HTTPException(status.HTTP_409_CONFLICT, "El periodo no está pendiente de aprobación de responsables")
        target = PeriodStatus.MANAGER_APPROVED if payload.decision == ApprovalDecision.APPROVED else PeriodStatus.COMMISSIONS_IMPORTED
    else:  # HR
        if user.role not in (Role.HR, Role.ADMIN):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo RRHH puede validar a nivel HR")
        if period.status != PeriodStatus.MANAGER_APPROVED:
            raise HTTPException(status.HTTP_409_CONFLICT, "El periodo no está aprobado por responsables")
        target = PeriodStatus.HR_APPROVED if payload.decision == ApprovalDecision.APPROVED else PeriodStatus.PENDING_MANAGER_APPROVAL

    db.add(Approval(
        period_id=period.id, level=level, approver_id=user.id,
        scope_company_id=user.scope_company_id, scope_department_id=user.scope_department_id,
        decision=payload.decision, comment=payload.comment,
    ))
    workflow.transition(db, period, target, actor_id=user.id, note=f"{level.value} {payload.decision.value}: {payload.comment or ''}")
    db.commit()
    db.refresh(period)
    return period


# --- 4. Envío a la gestoría ---
@router.post("/{period_id}/send-to-gestoria", response_model=PeriodOut)
def send_to_gestoria(
    period_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.HR)),
):
    period = _get_period(db, period_id)
    if period.status != PeriodStatus.HR_APPROVED:
        raise HTTPException(status.HTTP_409_CONFLICT, "El periodo debe estar validado por RRHH antes de enviar a la gestoría")
    last_import: CommissionImport | None = (
        db.query(CommissionImport).filter(CommissionImport.period_id == period.id)
        .order_by(CommissionImport.uploaded_at.desc()).first()
    )
    attachment = None
    if last_import:
        from pathlib import Path
        attachment = Path(last_import.stored_path)
    total = sum(float(l.amount) for imp in period.commission_imports for l in imp.lines)
    email.send(
        db,
        to=settings.gestoria_email,
        subject=f"Comisiones nómina {period.code} — Grupo",
        body=(f"Adjuntamos el fichero de comisiones del periodo {period.code}.\n"
              f"Importe total de comisiones: {total:,.2f} €.\n"
              f"Por favor, procesad las nóminas y devolved el Excel resumen. Gracias."),
        attachment=attachment,
        actor_id=user.id,
    )
    workflow.transition(db, period, PeriodStatus.SENT_TO_GESTORIA, actor_id=user.id, note=f"Enviado a {settings.gestoria_email}")
    db.commit()
    db.refresh(period)
    return period


# --- 5. Recepción del Excel de nóminas de la gestoría ---
@router.post("/{period_id}/payroll", response_model=ImportResult)
def upload_payroll(
    period_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.HR, Role.ACCOUNTING)),
):
    period = _get_period(db, period_id)
    if period.status not in (PeriodStatus.SENT_TO_GESTORIA, PeriodStatus.PAYROLL_RECEIVED):
        raise HTTPException(status.HTTP_409_CONFLICT, "El periodo no está a la espera del fichero de nóminas")
    path = _save_upload(file, f"nominas_{period.code}")
    try:
        imp = excel_payroll.ingest(db, period_id=period.id, filename=file.filename, stored_path=path, uploaded_by=user.id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))
    if period.status == PeriodStatus.SENT_TO_GESTORIA:
        workflow.transition(db, period, PeriodStatus.PAYROLL_RECEIVED, actor_id=user.id, note=f"Recibido {file.filename}")
    db.commit()
    unmatched = sum(1 for l in imp.lines if l.employee_id is None)
    return ImportResult(import_id=imp.id, row_count=imp.row_count, unmatched=unmatched)


# --- 6. Validación contra el maestro ---
@router.post("/{period_id}/validate", response_model=ValidationReport)
def validate_payroll(
    period_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ACCOUNTING, Role.HR)),
):
    period = _get_period(db, period_id)
    imp: PayrollImport | None = (
        db.query(PayrollImport).filter(PayrollImport.period_id == period.id)
        .order_by(PayrollImport.uploaded_at.desc()).first()
    )
    if not imp:
        raise HTTPException(status.HTTP_409_CONFLICT, "No hay fichero de nóminas cargado")
    report = validation.validate_payroll_import(db, imp)
    if report.ok and period.status == PeriodStatus.PAYROLL_RECEIVED:
        workflow.transition(db, period, PeriodStatus.PAYROLL_VALIDATED, actor_id=user.id, note="Validación OK")
    db.commit()
    return report


# --- 7. Generación del asiento de Autoline ---
@router.post("/{period_id}/journal", response_model=JournalEntryOut)
def generate_journal(
    period_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ACCOUNTING)),
):
    period = _get_period(db, period_id)
    if period.status != PeriodStatus.PAYROLL_VALIDATED:
        raise HTTPException(status.HTTP_409_CONFLICT, "El periodo debe estar validado antes de generar el asiento")
    imp: PayrollImport | None = (
        db.query(PayrollImport).filter(PayrollImport.period_id == period.id)
        .order_by(PayrollImport.uploaded_at.desc()).first()
    )
    entry = autoline_export.build_journal(db, period, imp)
    entry.generated_by = user.id
    if not entry.balanced:
        db.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            f"El asiento no cuadra: debe={entry.total_debit} haber={entry.total_credit}")
    autoline_export.export_xlsx(db, period, entry)
    workflow.transition(db, period, PeriodStatus.JOURNAL_GENERATED, actor_id=user.id, note="Asiento generado")
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/{period_id}/journal", response_model=JournalEntryOut)
def get_journal(period_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    entry = (
        db.query(JournalEntry).filter(JournalEntry.period_id == period_id)
        .order_by(JournalEntry.generated_at.desc()).first()
    )
    if not entry:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No hay asiento generado")
    return entry


@router.get("/{period_id}/journal/export")
def download_journal(period_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    entry = (
        db.query(JournalEntry).filter(JournalEntry.period_id == period_id)
        .order_by(JournalEntry.generated_at.desc()).first()
    )
    if not entry or not entry.export_filename:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No hay fichero de asiento exportado")
    path = settings.storage_dir / entry.export_filename
    if not path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fichero no disponible")
    return FileResponse(path, filename=entry.export_filename,
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.post("/{period_id}/close", response_model=PeriodOut)
def close_period(
    period_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ACCOUNTING)),
):
    period = _get_period(db, period_id)
    workflow.transition(db, period, PeriodStatus.CLOSED, actor_id=user.id, note="Periodo cerrado")
    db.commit()
    db.refresh(period)
    return period
