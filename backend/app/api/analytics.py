"""Endpoints de analítica para explotación BI (Power BI)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..security import get_current_user
from ..services import analytics

router = APIRouter(prefix="/api/analytics", tags=["analitica"])


@router.get("/cost")
def cost_by_dimension(
    dimension: str = Query("company", pattern="^(company|cost_center|department|concept|period)$"),
    period: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return {"dimension": dimension, "period": period, "data": analytics.cost_by_dimension(db, dimension, period)}


@router.get("/fixed-vs-variable")
def fixed_vs_variable(
    period: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return analytics.fixed_vs_variable(db, period)
