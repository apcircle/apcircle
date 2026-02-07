# Glosario de Negocio & Procesos — Plataforma de Gobierno de Datos

Aplicacion web completa para gestionar el glosario de terminos de negocio y los
procesos organizacionales, con funcionalidades de gobierno de datos a nivel inicial.

## Funcionalidades

### Glosario de Terminos
- CRUD completo de terminos de negocio
- Definicion, alcance, categoria y estado (Borrador/Revision/Aprobado/Obsoleto)
- Clasificacion de sensibilidad (Publico/Interno/Confidencial/Restringido)
- Asignacion de roles de gobierno: Data Owner, Data Steward, Data Custodian
- Reglas de calidad de datos por termino
- Sistemas relacionados
- Busqueda y filtrado por categoria y estado

### Procesos de Negocio
- CRUD completo de procesos
- Descripcion, objetivo, pasos, entradas, salidas, KPIs
- Vinculacion de terminos del glosario a cada proceso
- **Deteccion automatica de terminos**: al visualizar un proceso, los terminos del
  glosario aparecen resaltados y al hacer clic se muestra un popup con la definicion
  completa, Data Owner, Data Steward, sensibilidad, reglas de calidad, etc.
- Filtrado por estado y departamento

### Dashboard
- Metricas: total de terminos, aprobados, en borrador, procesos activos
- Distribucion por categorias
- Accesos rapidos

### Busqueda Global
- Busqueda unificada en glosario y procesos

### Onboarding
- Guia de introduccion al gobierno de datos
- Explicacion de roles (Data Owner, Steward, Custodian)
- Instrucciones de uso de la plataforma

## Stack Tecnologico

- **Frontend/Backend**: Next.js 16 (App Router) + TypeScript
- **Base de datos**: PostgreSQL 16
- **ORM**: Prisma 7 con adapter PostgreSQL nativo
- **UI**: Tailwind CSS 4 + Lucide Icons
- **Contenedores**: Docker Compose

## Inicio Rapido

### Opcion 1: Docker Compose (recomendado)

```bash
# Desde la raiz del proyecto
docker-compose up -d
```

Esto levanta PostgreSQL y la aplicacion en http://localhost:3000

### Opcion 2: Desarrollo local

1. **Levantar PostgreSQL** (Docker o instalacion local):
```bash
docker run -d --name glossary-db \
  -e POSTGRES_USER=glossary_user \
  -e POSTGRES_PASSWORD=glossary_pass \
  -e POSTGRES_DB=glossary_db \
  -p 5432:5432 \
  postgres:16-alpine
```

2. **Instalar dependencias**:
```bash
cd app
npm install
```

3. **Configurar variables de entorno**:
Editar `app/.env` si es necesario:
```
DATABASE_URL="postgresql://glossary_user:glossary_pass@localhost:5432/glossary_db?schema=public"
```

4. **Ejecutar migraciones**:
```bash
npm run db:migrate
```

5. **Cargar datos de ejemplo** (opcional):
```bash
npm run db:seed
```

6. **Iniciar en desarrollo**:
```bash
npm run dev
```

La aplicacion estara disponible en http://localhost:3000

## Scripts disponibles

| Comando           | Descripcion                              |
|-------------------|------------------------------------------|
| `npm run dev`     | Servidor de desarrollo                   |
| `npm run build`   | Build de produccion                      |
| `npm run start`   | Servidor de produccion                   |
| `npm run db:migrate` | Ejecutar migraciones de Prisma        |
| `npm run db:seed` | Cargar datos de ejemplo                  |
| `npm run db:reset`| Resetear base de datos                   |
| `npm run db:studio`| Abrir Prisma Studio (GUI de la BD)      |

## Estructura del Proyecto

```
app/
  prisma/
    schema.prisma          # Esquema de la base de datos
    seed.ts                # Datos de ejemplo
  src/
    app/
      api/
        glossary/          # API REST del glosario
        processes/         # API REST de procesos
        stats/             # API de estadisticas
      glossary/            # Pagina del glosario
      processes/           # Pagina de procesos
      search/              # Busqueda global
      onboarding/          # Guia de onboarding
      page.tsx             # Dashboard
      layout.tsx           # Layout principal
    components/
      Sidebar.tsx          # Navegacion lateral
      GlossaryTooltip.tsx  # Tooltip de terminos en procesos
      Modal.tsx            # Modal reutilizable
      StatusBadge.tsx      # Badge de estado
      SensitivityBadge.tsx # Badge de sensibilidad
    lib/
      prisma.ts            # Cliente de Prisma
docker-compose.yml         # Orquestacion de contenedores
```

## Modelo de Datos

- **GlossaryTerm**: Terminos del glosario con definicion, alcance, gobierno y clasificacion
- **BusinessProcess**: Procesos de negocio con pasos, E/S, KPIs y metadata
- **ProcessGlossaryTerm**: Relacion N:M entre procesos y terminos
