# Nómina Hub — Plataforma de orquestación de nóminas para grupo multimarca de automoción

Plataforma que orquesta el ciclo completo de nóminas de un grupo de concesionarios:
ingesta del Excel de comisiones extraído de los sistemas internos, validación por la
jerarquía de responsables, validación de RRHH, envío a la gestoría externa, recepción
del Excel de nóminas, validación contra el maestro de empleados, **generación del fichero
de asiento contable para DMS Autoline** (cuentas y centros de coste separados por concepto:
salario fijo, variable y seguridad social) y exposición de datos para análisis en Power BI.

> Estado: **MVP funcional + documentación de diseño**. Pensado como base sobre la que iterar.

## ¿Qué problema resuelve?

Hoy el proceso es manual y frágil:

```
Sistemas internos ──(Excel comisiones)──► Gestoría ──(Excel nóminas)──► Persona monta a mano
                                                                          el asiento de Autoline
```

Nómina Hub convierte ese flujo en un proceso trazable, con aprobaciones, validación de
datos y generación automática del asiento contable:

```
Sistemas ─► [Ingesta] ─► [Aprob. Responsables] ─► [Aprob. RRHH] ─► [Envío Gestoría]
   ─► [Recepción nóminas] ─► [Validación vs maestro] ─► [Asiento Autoline .xlsx] ─► [Power BI]
```

## Arquitectura (resumen)

- **Backend:** Python 3.11 + FastAPI + SQLAlchemy.
- **Base de datos:** PostgreSQL en producción; SQLite por defecto para arranque local sin dependencias.
- **Ingesta/Exportación Excel:** openpyxl / pandas.
- **Autenticación:** JWT + RBAC (roles y ámbito por sede/departamento).
- **Integraciones:** conector Factorial (opcional, para sincronizar jerarquía y altas/bajas),
  envío de correo SMTP a la gestoría, exposición de vistas analíticas para Power BI.
- **Frontend MVP:** interfaz web ligera servida con Jinja2 (login, panel, detalle de periodo,
  acciones de aprobación y exportación). Preparada para sustituir por SPA (React) más adelante.

Documentación detallada en [`docs/`](docs/):

| Documento | Contenido |
|-----------|-----------|
| [`01-arquitectura.md`](docs/01-arquitectura.md) | Visión, componentes, despliegue, seguridad |
| [`02-modelo-datos.md`](docs/02-modelo-datos.md) | Entidades, relaciones, cuentas contables |
| [`03-flujo-y-roles.md`](docs/03-flujo-y-roles.md) | Máquina de estados, roles, permisos |
| [`04-integraciones.md`](docs/04-integraciones.md) | Factorial, email, Autoline, Power BI |
| [`05-roadmap.md`](docs/05-roadmap.md) | Plan por fases |

## Arranque rápido (local, sin Docker)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed            # crea BD SQLite, datos de ejemplo y un Excel de comisiones de muestra
uvicorn app.main:app --reload
```

Abre http://localhost:8000 — interfaz web. API y documentación interactiva en
http://localhost:8000/docs.

Usuarios de ejemplo (creados por el seed):

| Email | Rol | Contraseña |
|-------|-----|-----------|
| director@grupo.com | ADMIN | demo1234 |
| jefe.ventas@grupo.com | MANAGER (Ventas/Sede Norte) | demo1234 |
| rrhh@grupo.com | HR | demo1234 |
| conta@grupo.com | ACCOUNTING | demo1234 |

## Arranque con Docker (PostgreSQL)

```bash
docker compose up --build
# luego, una vez arrancado:
docker compose exec api python -m app.seed
```

## Flujo de demostración (end-to-end)

1. **Login** como `jefe.ventas@grupo.com`.
2. Crea un **periodo** (ej. `2026-05`) y **sube el Excel de comisiones** de muestra
   (`backend/storage/ejemplo_comisiones.xlsx`, generado por el seed).
3. El responsable **valida** las comisiones de su ámbito → pasa a RRHH.
4. Login como `rrhh@grupo.com`: **valida** → habilita el botón **Enviar a gestoría**.
5. Pulsa **Enviar a gestoría** (envía email con el Excel; en demo se registra el envío).
6. Sube el **Excel de nóminas devuelto** (`backend/storage/ejemplo_nominas_gestoria.xlsx`).
   El sistema **valida** contra el maestro (empleados que faltan, cuentas sin configurar, importes).
7. Login como `conta@grupo.com`: **genera el asiento de Autoline** y **descarga el .xlsx**.
8. Consulta los endpoints `/api/analytics/*` (lo que conectarías desde Power BI).

## Tests

```bash
cd backend && pytest -q
```

Cubren el núcleo de valor: parseo del Excel de comisiones, validación contra maestro
y cuadre del asiento contable (debe == haber).
