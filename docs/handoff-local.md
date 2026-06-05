# Handoff — continuar Nómina Hub en sesión local

> Documento de traspaso entre la sesión en la nube y una sesión local de Claude Code.
> Si trabajas en local: haz `git pull` de la rama `claude/payroll-processing-app-BQ4kj` y pide a
> Claude Code que lea este fichero antes de empezar.

## 1. Quién y qué

- **Cliente:** Grupo Unione — automoción multimarca (varias marcas: BYD, OMODA, Mitsubishi,
  Moovers Cars…), varias sedes, **DMS Autoline (Kerridge/CDK)**, gestoría externa.
- **Objetivo:** plataforma **Nómina Hub** que orquesta el ciclo de nóminas:
  `Excel comisiones → aprobación responsables → RRHH → envío a gestoría → Excel nóminas devuelto
  → validación contra maestro → asiento contable Autoline (cuentas y centros de coste por
  concepto: fijo, variable, SS) → analítica Power BI`.
- **Rol del interlocutor:** Director de Sistemas y Transformación Digital.

## 2. Estado actual (lo que YA existe)

- Repo: **apcircle/apcircle**, rama **`claude/payroll-processing-app-BQ4kj`** (PR #1).
- **MVP funcional** en `backend/` (FastAPI + SQLAlchemy + SQLite/PostgreSQL):
  - Modelo de datos: `backend/app/models.py`, enums en `backend/app/enums.py`.
  - Ingesta Excel comisiones: `backend/app/services/excel_commissions.py`.
  - Ingesta Excel nóminas (gestoría): `backend/app/services/excel_payroll.py`.
  - Validación contra maestro: `backend/app/services/validation.py` + `mapping.py`.
  - **Construcción del asiento + export Autoline:** `backend/app/services/autoline_export.py`.
  - Máquina de estados: `backend/app/services/workflow.py`.
  - RBAC + auth propia (JWT): `backend/app/security.py`.
  - Conector Factorial: `backend/app/services/factorial.py` (modos `stub`/`live`).
  - Email a gestoría: `backend/app/services/email.py`.
  - Analítica (Power BI): `backend/app/services/analytics.py` + `api/analytics.py`.
  - UI web (Jinja2) en `backend/app/templates/`.
  - Seed + Excel de muestra: `backend/app/seed.py`.
  - Tests (13, verdes): `backend/tests/`.
- Documentación de diseño: `docs/01..05`.
- Arranque: `cd backend && pip install -r requirements.txt && python -m app.seed && uvicorn app.main:app --reload`.
  Usuarios demo (`demo1234`): director@grupo.com (ADMIN), jefe.ventas@grupo.com (MANAGER),
  rrhh@grupo.com (HR), conta@grupo.com (ACCOUNTING).

## 3. Cómo se construye el asiento HOY (lógica del MVP, a contrastar con la realidad)

En `autoline_export.build_journal` (modelo PGC España, cuadre garantizado):

```
DEBE                                   HABER
640000 Salario fijo        (CC)        465000 Líquido a pagar
640001 Salario variable    (CC)        475100 HP acreedora IRPF
642000 SS a cargo empresa  (CC)        476000 Organismos SS (SS trab. + SS empresa)
```
- La SS empresa hace **doble apunte** (gasto 642 al debe + deuda 476 al haber).
- Cuentas y centros de coste son configurables vía `AccountingMapping` (por empleado o por
  departamento). El layout de exportación está aislado en `autoline_export.AUTOLINE_COLUMNS` +
  `export_xlsx` (genérico, **pendiente** de sustituir por el real de su Autoline).

## 4. Factorial — VALIDADO contra el tenant real (solo lectura)

- **Auth:** header `x-api-key` → `FACTORIAL_AUTH_SCHEME=api_key`.
- **Endpoint empleados:** `/api/v2/resources/employees/employees`.
- **base_url:** `https://api.factorialhr.com` · **company_id:** 186970 · 540 empleados.
- **Cruce de empleados = DNI/NIE** (`identifier`) → matching del maestro por `national_id`
  (NO por `company_identifier`). Es el código común entre Factorial, gestoría y Autoline.
- **Mapeo de campos:** `factorial_id←id`, `full_name←full_name`, `email←email/login_email`,
  `national_id←identifier`, `manager_id←manager_id`, `company←legal_entity_id`,
  `sede←location_id`, baja←`terminated_on`/`active`.
- **Estructura organizativa real (sin PII):**
  - **9 sociedades** (`legal_entities`, CIF en `tin`) → `Company`:
    AUNITEC (223607), AUTOKRATOR (192606), AUTOMOCION TALAVERA COMERCIAL (192707),
    AUTOTRAK COMERCIAL (192690), EJE OCCIDENTAL DE CAMIONES (192709), UNIONE DRIVE (262411),
    UNIONE MOTION (189968), UNIONE MOVILIDAD (192716), VISAUTO (192708).
  - **26 sedes** (`locations`, ciudad+marca) → dimensión sede (`location_id`).
  - **16 departamentos** (`teams`, con `employee_ids` y `lead_ids`) → `Department` (+ responsable).
  - **No hay endpoint de cost centers** → centros de coste contables se mantienen en el maestro.
- **Cambios pendientes en `services/factorial.py`:** `_normalize` debe usar `identifier` como DNI
  y casar por DNI; mapear `legal_entity_id→Company` y `location_id→sede`; añadir 2ª llamada a
  `teams` para `Department`. (`_live_headers` ya soporta `x-api-key`.)
- **Config live:** `FACTORIAL_MODE=live`, `FACTORIAL_API_KEY=<secreto>`,
  `FACTORIAL_AUTH_SCHEME=api_key`, `FACTORIAL_EMPLOYEES_PATH=/api/v2/resources/employees/employees`.

## 5. Decisiones tomadas

- **Auth/usuarios propios (JWT)** para el MVP; **SSO EntraID** en Fase 1.
- **Maestro de empleados propio** = fuente de verdad contable; Factorial = jerarquía + altas/bajas.
- Cruce por **DNI/NIE**.

## 6. Trabajo PENDIENTE (lo que toca hacer ahora, con los ficheros locales)

1. **Analizar los ficheros reales** (en la carpeta local del usuario):
   - Excel(es) de **comisiones** de sus sistemas.
   - Excel(es) de la **gestoría** (puede haber varios formatos por marca/sociedad).
   - El **asiento de nóminas** real que suben hoy a Autoline (referencia para validar).
   - El **proyecto/plantilla del layout de Autoline** (columnas, orden, fecha, importes,
     separador, codificación, reglas del Nominal Journal Import).
2. **Informe** en `docs/06-analisis-nomina.md`: inventario de ficheros, cómo se construye su
   asiento real, conceptos contables usados (incl. dietas, embargos, especie, anticipos…),
   y **diferencias vs el MVP**.
3. **Adaptar el código** (con confirmación):
   - `excel_payroll.py`: parsers por formato real (ampliar `CONCEPT_COLUMNS` / mapeo configurable).
   - `enums.py`: añadir conceptos que falten.
   - `autoline_export.build_journal`: ajustar semántica real manteniendo cuadre Debe=Haber.
   - `autoline_export.AUTOLINE_COLUMNS`/`export_xlsx`: **sustituir por el layout real**.
   - `seed`/`AccountingMapping`: cargar las 9 sociedades reales, sus `autoline_company_code` y el
     plan de cuentas/centros real.
4. **Factorial live:** aplicar los cambios del §4 y probar
   `POST /api/integrations/factorial/sync?company_id=...`.

## 7. Verificación

- Reproducir el asiento desde el Excel de gestoría y **diff línea a línea** contra el asiento real.
- `pytest -q` (13 actuales + nuevos por formato real).
- E2E por la API: login → subir nómina → validar → generar asiento → descargar.

## 8. ⚠️ Seguridad

- **Rotar la API key de Factorial** (se pegó en un chat). Guardarla solo como secreto de entorno
  (`.env` local fuera de git / gestor de secretos), nunca en código ni en chats.
