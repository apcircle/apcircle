# 02 — Modelo de datos

## Diagrama de entidades

```
Company (sede/sociedad)
  └─< CostCenter (centro de coste)
  └─< Department
        └─< Employee >── manager_id (auto-ref, jerarquía)
                └─< AccountingMapping (cuenta + centro de coste por concepto)

User >── role, scope (sede/depto)

PayrollPeriod (mes de nómina)
  └─< CommissionImport ─< CommissionLine
  └─< PayrollImport (de gestoría) ─< PayrollLine
  └─< Approval (responsable / RRHH)
  └─< JournalEntry ─< JournalLine
  └─< StateTransition  (historial de la máquina de estados)

AuditLog  (transversal)
```

## Entidades principales

### Company
Sociedad/sede del grupo (cada marca/concesionario puede ser una sociedad distinta).
- `id`, `code`, `name`, `tax_id` (CIF), `autoline_company_code`

### CostCenter
Centro de coste para imputación analítica (taller, ventas VN, ventas VO, postventa, recambios…).
- `id`, `company_id`, `code`, `name`

### Department
Departamento funcional (Ventas, Postventa, Recambios, Administración…).
- `id`, `company_id`, `name`, `default_cost_center_id`

### Employee — **maestro de empleados (fuente de verdad contable)**
- `id`, `factorial_id` (nullable), `employee_code`, `full_name`, `national_id` (DNI/NIE)
- `company_id`, `department_id`, `cost_center_id`
- `manager_id` (auto-referencia → jerarquía de aprobación)
- `active`, `email`, `created_at`, `updated_at`

### AccountingMapping — cuentas de contabilización por concepto
Define, para un empleado (o por defecto a nivel de departamento), **qué cuenta contable y
qué centro de coste** se usan para cada concepto de nómina. Es la pieza que permite que el
asiento salga con cuentas y centros separados.

- `id`, `scope` (`EMPLOYEE` | `DEPARTMENT`), `employee_id` (nullable), `department_id` (nullable)
- `concept` (enum `PayrollConcept`)
- `account` (cuenta contable, ej. `640000`)
- `cost_center_id`
- `side` (`DEBIT` | `CREDIT`)

Resolución: primero se busca mapeo a nivel `EMPLOYEE`; si no existe, se usa el del
`DEPARTMENT`. Si no hay ninguno → **error de validación** (cuenta sin configurar).

### PayrollConcept (enum)
Conceptos que componen la nómina y el asiento:

| Concepto | Naturaleza | Cuenta típica (configurable) | Lado |
|----------|-----------|------------------------------|------|
| `SALARIO_FIJO` | Gasto | 640000 Sueldos y salarios | DEBE |
| `SALARIO_VARIABLE` | Gasto | 640001 Retrib. variable/comisiones | DEBE |
| `SEGURIDAD_SOCIAL_EMPRESA` | Gasto | 642000 SS a cargo empresa | DEBE |
| `RETENCION_IRPF` | Pasivo | 475100 HP acreedora retenciones | HABER |
| `SEGURIDAD_SOCIAL_TRABAJADOR` | Pasivo | 476000 Org. SS acreedores | HABER |
| `LIQUIDO_A_PAGAR` | Pasivo | 465000 Remun. pendientes de pago | HABER |
| `ANTICIPOS` | Activo/menos pasivo | 460000 Anticipos remuneraciones | (config) |

> El asiento cuadra cuando: `Σ DEBE (gastos) = Σ HABER (líquido + retenciones + SS organismos)`.
> Ver `04-integraciones.md` §Autoline para el detalle del cuadre.

### PayrollPeriod
Periodo de nómina (normalmente mensual).
- `id`, `code` (`2026-05`), `company_id` (nullable = grupo), `status` (enum `PeriodStatus`)
- `created_by`, `created_at`, fechas de cada hito.

### CommissionImport / CommissionLine
El Excel de comisiones extraído de los sistemas internos.
- `CommissionImport`: `id`, `period_id`, `filename`, `uploaded_by`, `uploaded_at`, `row_count`, `status`
- `CommissionLine`: `id`, `import_id`, `employee_code`, `employee_id` (resuelto), `department`,
  `concept`, `amount`, `notes`, `validation_status`

### PayrollImport / PayrollLine
El Excel resumen devuelto por la gestoría.
- `PayrollImport`: `id`, `period_id`, `filename`, `uploaded_by`, `uploaded_at`, `row_count`, `status`
- `PayrollLine`: `id`, `import_id`, `employee_code`, `employee_id` (resuelto), `concept`,
  `amount`, `validation_status`, `validation_message`

### Approval
Registro de validaciones (responsable de ámbito y RRHH).
- `id`, `period_id`, `level` (`MANAGER` | `HR`), `approver_id`, `scope` (sede/depto), `decision`
  (`APPROVED` | `REJECTED`), `comment`, `decided_at`

### JournalEntry / JournalLine — el asiento de Autoline
- `JournalEntry`: `id`, `period_id`, `company_id`, `entry_date`, `total_debit`, `total_credit`,
  `balanced` (bool), `generated_by`, `generated_at`, `export_filename`
- `JournalLine`: `id`, `entry_id`, `account`, `cost_center_code`, `concept`, `debit`, `credit`,
  `narrative`, `employee_code`

### StateTransition
Historial de la máquina de estados del periodo.
- `id`, `period_id`, `from_status`, `to_status`, `actor_id`, `at`, `note`

### User
- `id`, `email`, `full_name`, `hashed_password`, `role` (enum `Role`), `active`
- `scope_company_id` (nullable), `scope_department_id` (nullable) → ámbito de un MANAGER

### AuditLog
- `id`, `actor_id`, `action`, `entity_type`, `entity_id`, `metadata` (JSON), `at`

## Notas de integridad

- `CommissionLine.employee_id` y `PayrollLine.employee_id` se resuelven contra el maestro por
  `employee_code` (y como respaldo por `national_id`). Si no resuelve → fila marcada
  `UNMATCHED` y bloquea la generación del asiento hasta corregir.
- El borrado de `Employee` es lógico (`active=false`), nunca físico, para preservar histórico.
- Los importes se almacenan en `Numeric(12,2)` para evitar errores de coma flotante.
