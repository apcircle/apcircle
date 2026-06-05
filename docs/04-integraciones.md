# 04 — Integraciones

## 1. Factorial (jerarquía y maestro de empleados) — opcional

**Estrategia:** maestro propio como fuente de verdad contable; Factorial como fuente opcional
de jerarquía y altas/bajas. El conector es un *adapter* (`services/factorial.py`) con dos modos:

- `FACTORIAL_MODE=stub` (por defecto): devuelve datos simulados, sin red. Útil para desarrollo y tests.
- `FACTORIAL_MODE=live`: cliente HTTP real contra la API de Factorial (`services/factorial.py`).

**Configuración (modo live):**

| Variable | Por defecto | Uso |
|----------|-------------|-----|
| `FACTORIAL_API_KEY` | — | credencial (requerida en live) |
| `FACTORIAL_BASE_URL` | `https://api.factorialhr.com` | base de la API |
| `FACTORIAL_EMPLOYEES_PATH` | `/api/v2/resources/employees/employees` | endpoint de empleados (parametrizable porque la versión de la API cambia) |
| `FACTORIAL_AUTH_SCHEME` | `api_key` | `api_key` (header `x-api-key`) o `bearer` (`Authorization: Bearer`) |
| `FACTORIAL_PAGE_SIZE` | `100` | tamaño de página (paginación automática) |
| `FACTORIAL_MAP_TEAM_TO_DEPARTMENT` | `true` | mapea el *team* de Factorial a un `Department` del maestro por nombre |

**Sincronización (`sync_employees`) — implementada:**
1. Descarga los empleados de Factorial **paginando** y los **normaliza** a un esquema interno
   (tolerante a variaciones de nombres de campo entre versiones de la API).
2. Hace *upsert* en el maestro por `factorial_id` (respaldo por `employee_code`):
   - Crea empleados nuevos; los que quedan sin departamento → **pendientes de configurar** (sin cuentas).
   - Actualiza nombre, email, estado activo y, opcionalmente, el departamento (vía *team*).
   - **Nunca** sobrescribe `account`/`cost_center`/`employee_code` (responsabilidad contable).
3. **Resuelve la jerarquía**: segunda pasada que enlaza `manager_id` a partir del manager de Factorial.
4. **Gestiona bajas**: los empleados con `factorial_id` que ya no aparecen (o terminados) se marcan
   `active=False` (borrado lógico, nunca físico).
5. Devuelve un informe: `created`, `updated`, `deactivated`, `managers_linked`, `pending_accounting_mapping`, `errors`.
   Si hay errores de conexión, la API hace *rollback* y responde `502` sin dejar cambios parciales.

> Roadmap: webhooks de Factorial para altas/bajas en tiempo real (hoy la sync es bajo demanda
> vía `POST /api/integrations/factorial/sync?company_id=...`, rol ADMIN).

> Si en el futuro se decide que Factorial sea la fuente de verdad total, basta con activar
> la sincronización completa; el modelo ya contempla `factorial_id` en `Employee`.

## 2. Envío de correo a la gestoría — SMTP

Servicio `services/email.py`. Configurable por entorno:

```
SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM, SMTP_TLS
GESTORIA_EMAIL=nominas@gestoria-ejemplo.es
```

- Si no hay SMTP configurado → **modo registro**: el envío se guarda en `audit_log` y se marca
  como enviado (para demo). Si hay SMTP → envío real con el Excel de comisiones adjunto.
- Plantilla con el resumen del periodo, importe total y nº de empleados.

## 3. Asiento contable para DMS Autoline

### Construcción del asiento (`services/autoline_export.py`)

A partir de las `PayrollLine` validadas, por cada empleado y concepto:
1. Se resuelve el **mapeo contable** (`AccountingMapping`): cuenta + centro de coste + lado.
2. Se agrupan las líneas por `(cuenta, centro de coste, lado)` para un asiento compacto,
   **o** se mantiene el detalle por empleado (configurable `AUTOLINE_DETAIL_LEVEL=summary|employee`).
3. Se calcula el cuadre:

```
DEBE  = SALARIO_FIJO + SALARIO_VARIABLE + SEGURIDAD_SOCIAL_EMPRESA
HABER = LIQUIDO_A_PAGAR + RETENCION_IRPF + SEGURIDAD_SOCIAL_TRABAJADOR + SS_EMPRESA(org.)
```

> El líquido a pagar = devengos − retención IRPF − SS trabajador. La SS empresa es gasto (DEBE)
> y a la vez deuda con la TGSS (HABER). El servicio valida `total_debit == total_credit` y marca
> `JournalEntry.balanced`. Si no cuadra, no se permite exportar (se devuelve el detalle del descuadre).

### Layout de exportación Autoline (configurable)

El fichero de importación de asientos de Autoline (Kerridge/CDK) se genera como `.xlsx` con un
layout parametrizable (`AUTOLINE_COLUMNS` en config). Columnas por defecto del MVP:

| Columna | Origen |
|---------|--------|
| `Company` | `company.autoline_company_code` |
| `Account` | `JournalLine.account` |
| `CostCentre` | `JournalLine.cost_center_code` |
| `Period` | código del periodo (`2026-05`) |
| `Date` | `JournalEntry.entry_date` |
| `Debit` | `JournalLine.debit` |
| `Credit` | `JournalLine.credit` |
| `Narrative` | `JournalLine.narrative` (concepto + periodo) |
| `Reference` | `NOM-{period}` |

> El layout exacto se ajustará al import de asientos de vuestra instalación de Autoline
> (Nominal Ledger → Journal Import). Está aislado en una sola función para cambiarlo sin
> tocar la lógica de negocio.

## 4. Power BI / explotación analítica

Dos vías, complementarias:

1. **Endpoints analíticos** (`/api/analytics/*`) que devuelven agregados en JSON/CSV:
   - coste por sede / centro de coste / departamento / concepto / periodo,
   - evolución de retribución variable vs fija,
   - coste de seguridad social,
   - top de comisiones, etc.
   Power BI puede consumirlos con conector Web/OData.

2. **Acceso directo a la BD (recomendado para BI a escala):** crear un usuario de solo lectura
   en PostgreSQL y un conjunto de **vistas** (`vw_coste_nomina`, `vw_comisiones`, …) sobre las
   que Power BI conecta con DirectQuery. Las vistas desacoplan el esquema físico del modelo BI.

Esquema en estrella sugerido para el modelo de Power BI:
```
fact_payroll_line (importe, debit/credit) ─┬─ dim_employee
                                            ├─ dim_company / dim_cost_center
                                            ├─ dim_concept
                                            └─ dim_period (calendario)
```
