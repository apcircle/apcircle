# 03 — Flujo de aprobaciones y roles

## Máquina de estados del periodo de nómina

```
                 subir Excel comisiones
   DRAFT ───────────────────────────────────► COMMISSIONS_IMPORTED
                                                       │
                                  responsables validan (por ámbito)
                                                       ▼
                                            PENDING_MANAGER_APPROVAL
                                                       │
                                   todos los ámbitos aprobados
                                                       ▼
                                            MANAGER_APPROVED
                                                       │
                                          RRHH valida
                                                       ▼
                                            HR_APPROVED
                                                       │
                                   pulsar "Enviar a gestoría"
                                                       ▼
                                            SENT_TO_GESTORIA
                                                       │
                                 subir Excel nóminas devuelto
                                                       ▼
                                            PAYROLL_RECEIVED
                                                       │
                            validación contra maestro (OK)
                                                       ▼
                                            PAYROLL_VALIDATED
                                                       │
                              contabilidad genera asiento
                                                       ▼
                                            JOURNAL_GENERATED
                                                       │
                                    exportar / cerrar
                                                       ▼
                                            CLOSED
```

Estados de rechazo/retroceso:
- Cualquier validación puede **rechazar** → vuelve al estado anterior con comentario
  (`REJECTED` se registra en `Approval` y `StateTransition`).
- `PAYROLL_RECEIVED` con errores de validación → permanece ahí (no avanza a
  `PAYROLL_VALIDATED`) mostrando el informe de incidencias hasta corregir maestro/fichero.

Transiciones permitidas (`workflow.ALLOWED_TRANSITIONS`):

| Desde | Hacia | Acción | Rol que dispara |
|-------|-------|--------|-----------------|
| DRAFT | COMMISSIONS_IMPORTED | subir comisiones | MANAGER/ADMIN |
| COMMISSIONS_IMPORTED | PENDING_MANAGER_APPROVAL | enviar a aprobación | MANAGER/ADMIN |
| PENDING_MANAGER_APPROVAL | MANAGER_APPROVED | todos los ámbitos aprueban | MANAGER |
| MANAGER_APPROVED | HR_APPROVED | RRHH valida | HR |
| HR_APPROVED | SENT_TO_GESTORIA | enviar a gestoría | HR/ADMIN |
| SENT_TO_GESTORIA | PAYROLL_RECEIVED | subir nóminas | HR/ACCOUNTING |
| PAYROLL_RECEIVED | PAYROLL_VALIDATED | validación OK | ACCOUNTING |
| PAYROLL_VALIDATED | JOURNAL_GENERATED | generar asiento | ACCOUNTING |
| JOURNAL_GENERATED | CLOSED | cerrar periodo | ACCOUNTING/ADMIN |

## Roles

| Rol | Descripción | Capacidades clave |
|-----|-------------|-------------------|
| `ADMIN` | Dirección de Sistemas | Todo. Gestión de maestros, usuarios, configuración de cuentas y layout Autoline |
| `MANAGER` | Responsable de sede/departamento | Subir comisiones de su ámbito, validar/rechazar comisiones de su ámbito |
| `HR` | Recursos Humanos | Validar a nivel global, enviar a gestoría, subir nóminas |
| `ACCOUNTING` | Contabilidad | Validar nóminas vs maestro, generar y exportar el asiento Autoline |
| `VIEWER` | Consulta/BI | Solo lectura, acceso a analítica |

## RBAC con ámbito (scope)

Los permisos combinan **acción** + **ámbito**:

- Un `MANAGER` con `scope = (Sede Norte, Ventas)` solo ve y aprueba las líneas de comisión
  cuyo empleado pertenece a esa sede y departamento.
- `HR`, `ACCOUNTING`, `ADMIN` tienen ámbito global.
- La comprobación se centraliza en `security.require_role(...)` y
  `security.filter_by_scope(...)`.

Matriz de permisos (resumen):

| Acción | ADMIN | MANAGER | HR | ACCOUNTING | VIEWER |
|--------|:-----:|:-------:|:--:|:----------:|:------:|
| Ver periodos | ✓ | ✓ (ámbito) | ✓ | ✓ | ✓ |
| Subir comisiones | ✓ | ✓ (ámbito) | – | – | – |
| Aprobar comisiones | ✓ | ✓ (ámbito) | – | – | – |
| Validar RRHH | ✓ | – | ✓ | – | – |
| Enviar a gestoría | ✓ | – | ✓ | – | – |
| Subir nóminas | ✓ | – | ✓ | ✓ | – |
| Validar nóminas | ✓ | – | – | ✓ | – |
| Generar asiento | ✓ | – | – | ✓ | – |
| Gestionar maestros/config | ✓ | – | – | – | – |
| Analítica | ✓ | ✓ (ámbito) | ✓ | ✓ | ✓ |

## Notificaciones

Cada transición relevante puede disparar un email (servicio `email`):
- A los responsables cuando un periodo entra en `PENDING_MANAGER_APPROVAL`.
- A RRHH cuando pasa a `MANAGER_APPROVED`.
- A la gestoría al `SENT_TO_GESTORIA` (con el Excel adjunto).
- A contabilidad cuando se recibe el fichero de nóminas.

En el MVP las notificaciones se registran y, si hay SMTP configurado, se envían realmente.
