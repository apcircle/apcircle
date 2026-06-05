# 05 — Roadmap por fases

## Fase 0 — MVP (este entregable) ✅
- Modelo de datos completo (maestro, mapeos contables, periodos, importaciones, asiento).
- Ingesta del Excel de comisiones + normalización.
- Aprobación jerárquica (responsables) + validación RRHH.
- Acción "Enviar a gestoría" (email con adjunto / modo registro).
- Ingesta del Excel de nóminas devuelto por la gestoría.
- Validación contra maestro: empleados que faltan, cuentas sin configurar, importes.
- Generación del asiento Autoline (cuentas + centros de coste por concepto) y export `.xlsx`.
- RBAC con ámbito por sede/departamento.
- Conector Factorial (stub) + servicio de email + endpoints de analítica.
- UI web ligera para los distintos roles.
- Tests del núcleo (parseo, validación, cuadre del asiento).

## Fase 1 — Endurecimiento y producción
- PostgreSQL gestionado + migraciones con Alembic.
- SSO corporativo (Entra ID / OIDC) sustituyendo el JWT propio.
- Almacenamiento de ficheros en S3/Azure Blob.
- Conexión **live** real a Factorial + webhooks de altas/bajas.
- Configurador visual del mapeo de cuentas y del layout de Autoline (sin tocar código).
- Auditoría completa + panel de incidencias de validación.

## Fase 2 — Automatización e integración profunda
- Importación directa del asiento a Autoline (API/automatización) en lugar de Excel manual.
- Conciliación automática: cuadre contra el devengado previsto y alertas de desviación.
- Reglas de validación avanzadas (límites por convenio, topes de variable, controles de fraude).
- Flujos de aprobación configurables (N niveles, delegaciones, suplencias).

## Fase 3 — Analítica avanzada
- Vistas materializadas / data warehouse + modelo en estrella para Power BI.
- Cuadros de mando de coste de personal por marca/sede/centro de coste.
- Simulación de escenarios retributivos y *forecast* de coste laboral.
- Indicadores: coste comisión por venta, ratio variable/fijo, coste SS, absentismo (vía Factorial).

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|-----------|
| Formatos de Excel heterogéneos entre sistemas/gestoría | Mapeo de columnas configurable + validación estricta con informe de errores |
| Cuentas/centros mal configurados | Bloqueo de generación de asiento + informe de "pendientes de configurar" |
| Datos sensibles de retribución | RBAC con ámbito, cifrado, auditoría, mínimos privilegios (RGPD) |
| Dependencia de la gestoría | Maestro propio como fuente de verdad; el proceso no depende de su esquema |
| Cambios en el layout de Autoline | Layout aislado y parametrizable en un único punto |
```
