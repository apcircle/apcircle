"""Punto de entrada de la aplicación FastAPI."""
from __future__ import annotations

from fastapi import FastAPI

from .config import settings
from .database import init_db
from .api import analytics, auth, employees, periods, ui

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Plataforma de orquestación de nóminas para grupo multimarca de automoción.",
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/health", tags=["health"])
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "env": settings.environment}


app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(periods.router)
app.include_router(analytics.router)
app.include_router(ui.router)
