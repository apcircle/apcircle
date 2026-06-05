"""Interfaz web ligera (Jinja2). El navegador llama a la API con el token en cookie."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import authenticate, create_access_token

router = APIRouter(tags=["ui"], include_in_schema=False)
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    if not request.cookies.get("access_token"):
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
def do_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = authenticate(db, username, password)
    if not user:
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Credenciales inválidas"}, status_code=401
        )
    token = create_access_token(user)
    resp = RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    # No httponly: la UI lee el token para llamar a la API con Authorization Bearer.
    resp.set_cookie("access_token", token, max_age=60 * 60 * 8, samesite="lax")
    return resp


@router.get("/logout")
def logout():
    resp = RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    resp.delete_cookie("access_token")
    return resp


@router.get("/periodos/{period_id}", response_class=HTMLResponse)
def period_detail(request: Request, period_id: int):
    if not request.cookies.get("access_token"):
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("period.html", {"request": request, "period_id": period_id})
