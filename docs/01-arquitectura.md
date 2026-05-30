# 01 — Arquitectura

## 1. Visión

Nómina Hub es el sistema central que orquesta el proceso de nóminas del grupo, desde la
captura de comisiones hasta la contabilización en Autoline y la explotación analítica.
Su objetivo es **eliminar el trabajo manual y los errores** en la construcción del asiento
de nóminas, aportando **trazabilidad, control de aprobaciones y validación de datos**.

Principios de diseño:

- **El maestro de empleados es la fuente de verdad contable.** Las cuentas y centros de
  coste viven aquí, no en la gestoría ni en hojas sueltas.
- **Factorial es opcional y desacoplado.** Se integra como fuente de jerarquía/altas-bajas,
  pero el sistema funciona sin él. El conector es un *adapter* sustituible.
- **Cada paso deja rastro.** Toda transición de estado, importación y exportación queda
  auditada (quién, cuándo, qué).
- **El formato de salida es configurable.** El layout del asiento de Autoline y el mapeo de
  cuentas se parametrizan; no se hardcodean.

## 2. Componentes

```
┌──────────────────────────────────────────────────────────────────────────┐
│                            NÓMINA HUB (FastAPI)                            │
│                                                                            │
│  ┌────────────┐   ┌──────────────┐   ┌───────────────┐   ┌─────────────┐  │
│  │  API REST  │   │  UI Jinja2   │   │  Auth + RBAC  │   │  Auditoría  │  │
│  └─────┬──────┘   └──────┬───────┘   └───────┬───────┘   └──────┬──────┘  │
│        │                 │                   │                  │         │
│  ┌─────┴─────────────────┴───────────────────┴──────────────────┴──────┐ │
│  │                          Capa de Servicios                           │ │
│  │  ingesta_comisiones · ingesta_nominas · validacion · workflow ·      │ │
│  │  export_autoline · email · factorial · analytics                     │ │
│  └─────────────────────────────────┬───────────────────────────────────┘ │
│                                     │                                      │
│  ┌──────────────────────────────────┴──────────────────────────────────┐ │
│  │                    Modelo de datos (SQLAlchemy)                      │ │
│  └──────────────────────────────────┬──────────────────────────────────┘ │
└─────────────────────────────────────┼──────────────────────────────────────┘
                                       │
                  ┌────────────────────┼─────────────────────┐
                  │                    │                     │
            ┌─────┴─────┐        ┌─────┴──────┐        ┌──────┴──────┐
            │PostgreSQL │        │  Factorial │        │   SMTP /    │
            │           │        │    API     │        │  Gestoría   │
            └─────┬─────┘        └────────────┘        └─────────────┘
                  │
          ┌───────┴────────┐
          │   Power BI     │  (lectura sobre vistas/endpoints analíticos)
          └────────────────┘
```

### Capa de servicios (dónde está la lógica de negocio)

| Servicio | Responsabilidad |
|----------|-----------------|
| `excel_commissions` | Parsear y normalizar el Excel de comisiones de los sistemas internos |
| `excel_payroll` | Parsear el Excel de nóminas devuelto por la gestoría |
| `validation` | Reglas de validación: empleados que faltan, cuentas sin mapear, importes, descuadres |
| `workflow` | Máquina de estados del periodo + registro de transiciones |
| `autoline_export` | Construir las líneas del asiento (debe/haber, cuenta, centro de coste) y exportar a Excel |
| `email` | Envío SMTP a la gestoría con adjunto y plantilla |
| `factorial` | *Adapter* de sincronización de empleados/jerarquía (opcional) |
| `analytics` | Vistas agregadas para Power BI / consumo BI |

## 3. Modelo de despliegue

- **Contenedores:** `api` (FastAPI/uvicorn) + `db` (PostgreSQL). `docker-compose.yml` incluido.
- **Estado de ficheros:** los Excel subidos y generados se guardan en `storage/` (en producción,
  sustituible por S3/Azure Blob mediante una interfaz de almacenamiento).
- **Configuración:** 100% por variables de entorno (`.env`). Ver `.env.example`.
- **Escalado:** la API es *stateless* (sesión vía JWT), escalable horizontalmente detrás de un
  balanceador. La BD es el único estado.

## 4. Seguridad

- **Autenticación:** JWT firmado (HS256 en MVP; migrable a RS256/SSO corporativo / Entra ID).
- **Autorización:** RBAC con **ámbito**. Un MANAGER solo ve/aprueba su(s) sede(s) y
  departamento(s). Ver `03-flujo-y-roles.md`.
- **Datos sensibles:** la plataforma maneja datos de retribución (categoría especial a efectos
  organizativos). Recomendaciones:
  - Cifrado en tránsito (TLS) y en reposo (cifrado de disco / columnas sensibles).
  - Minimización: no almacenar más que lo necesario para contabilizar y analizar.
  - Acceso por rol con principio de mínimo privilegio y auditoría de accesos.
  - Retención y borrado conforme a normativa (RGPD/LOPDGDD).
- **Auditoría:** tabla `audit_log` con actor, acción, entidad, timestamp y metadatos.
- **Secretos:** credenciales de Factorial/SMTP fuera del código, en gestor de secretos.

## 5. Decisiones técnicas y porqués

| Decisión | Razón |
|----------|-------|
| FastAPI | Productividad, tipado, OpenAPI automático (útil para integraciones) |
| SQLAlchemy + SQLite/PostgreSQL | Mismo código, arranque local sin dependencias y producción robusta |
| Maestro propio de empleados | Independencia de la gestoría y de Factorial para la contabilización |
| Conector Factorial como adapter | Integración opcional y sustituible sin tocar el dominio |
| Export Autoline parametrizable | Cada DMS/empresa tiene su layout de importación de asientos |
| UI Jinja2 en MVP | Tangibilidad inmediata; frontera limpia para migrar a SPA |

## 6. Qué NO incluye el MVP (y está en el roadmap)

- SSO corporativo / Entra ID (MVP usa JWT propio).
- Conexión productiva real a la API de Factorial (incluye *adapter* + stub mockeado).
- Almacenamiento en S3/Azure Blob (MVP usa disco local).
- Firma/sellado del asiento e integración *push* directa a Autoline (MVP genera el Excel de importación).
- Vistas materializadas / *data warehouse* para BI a gran escala (MVP expone endpoints + vistas).
