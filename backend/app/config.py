"""Configuración de la aplicación, 100% por variables de entorno."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Nómina Hub"
    environment: str = "local"

    # Base de datos: SQLite por defecto para arranque local sin dependencias.
    database_url: str = f"sqlite:///{BASE_DIR / 'nominahub.db'}"

    # Seguridad
    secret_key: str = "cambia-esta-clave-en-produccion"
    access_token_expire_minutes: int = 60 * 8
    jwt_algorithm: str = "HS256"

    # Almacenamiento
    storage_dir: Path = STORAGE_DIR

    # Email / gestoría
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "nominahub@grupo.com"
    smtp_tls: bool = True
    gestoria_email: str = "nominas@gestoria-ejemplo.es"

    # Factorial
    factorial_mode: str = "stub"  # stub | live
    factorial_api_key: str | None = None
    factorial_base_url: str = "https://api.factorialhr.com/api/v1"

    # Autoline
    autoline_detail_level: str = "summary"  # summary | employee
    autoline_default_company_code: str = "01"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
