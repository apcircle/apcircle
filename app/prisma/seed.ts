import { PrismaClient } from "../src/generated/prisma/client";
import { PrismaPg } from "@prisma/adapter-pg";

const adapter = new PrismaPg(process.env.DATABASE_URL!);
const prisma = new PrismaClient({ adapter });

async function main() {
  // Seed glossary terms
  const terms = await Promise.all([
    prisma.glossaryTerm.upsert({
      where: { term: "Cliente" },
      update: {},
      create: {
        term: "Cliente",
        definition:
          "Persona física o jurídica que ha contratado o utiliza activamente uno o más productos o servicios de la organización.",
        scope: "Toda la organización",
        category: "Entidades",
        status: "APPROVED",
        dataOwner: "María García",
        dataOwnerEmail: "maria.garcia@empresa.com",
        dataSteward: "Carlos López",
        dataStewardEmail: "carlos.lopez@empresa.com",
        dataCustodian: "Equipo de Datos",
        sensitivity: "CONFIDENTIAL",
        qualityRules: "Debe tener NIF/CIF válido, nombre completo y al menos un dato de contacto",
        relatedSystems: "CRM, ERP, Plataforma de Facturación",
      },
    }),
    prisma.glossaryTerm.upsert({
      where: { term: "Producto" },
      update: {},
      create: {
        term: "Producto",
        definition:
          "Bien o servicio ofrecido por la organización que puede ser adquirido o contratado por un cliente.",
        scope: "Comercial, Marketing, Operaciones",
        category: "Entidades",
        status: "APPROVED",
        dataOwner: "Pedro Martínez",
        dataOwnerEmail: "pedro.martinez@empresa.com",
        dataSteward: "Laura Sánchez",
        dataStewardEmail: "laura.sanchez@empresa.com",
        sensitivity: "INTERNAL",
        qualityRules: "Código único, nombre, precio y categoría obligatorios",
        relatedSystems: "ERP, Catálogo Digital, E-commerce",
      },
    }),
    prisma.glossaryTerm.upsert({
      where: { term: "Factura" },
      update: {},
      create: {
        term: "Factura",
        definition:
          "Documento fiscal que acredita la entrega de un producto o la prestación de un servicio, junto con la fecha y el importe.",
        scope: "Finanzas, Contabilidad, Comercial",
        category: "Documentos",
        status: "APPROVED",
        dataOwner: "Ana Fernández",
        dataOwnerEmail: "ana.fernandez@empresa.com",
        dataSteward: "Roberto Díaz",
        dataStewardEmail: "roberto.diaz@empresa.com",
        sensitivity: "CONFIDENTIAL",
        qualityRules: "Número secuencial único, datos fiscales completos del cliente",
        relatedSystems: "ERP, Sistema de Facturación, Contabilidad",
      },
    }),
    prisma.glossaryTerm.upsert({
      where: { term: "KPI" },
      update: {},
      create: {
        term: "KPI",
        definition:
          "Indicador clave de rendimiento (Key Performance Indicator). Métrica cuantificable utilizada para evaluar el éxito de una actividad o proceso.",
        scope: "Toda la organización",
        category: "Métricas",
        status: "APPROVED",
        dataOwner: "Dirección General",
        dataSteward: "Business Intelligence",
        sensitivity: "INTERNAL",
        relatedSystems: "BI, Cuadro de Mando",
      },
    }),
    prisma.glossaryTerm.upsert({
      where: { term: "Data Owner" },
      update: {},
      create: {
        term: "Data Owner",
        definition:
          "Responsable de negocio que tiene la autoridad y responsabilidad sobre un conjunto de datos. Define las políticas de acceso, calidad y uso de los datos.",
        scope: "Gobierno de Datos",
        category: "Roles",
        status: "APPROVED",
        dataOwner: "CDO",
        dataSteward: "Oficina de Gobierno de Datos",
        sensitivity: "PUBLIC",
      },
    }),
    prisma.glossaryTerm.upsert({
      where: { term: "Data Steward" },
      update: {},
      create: {
        term: "Data Steward",
        definition:
          "Persona responsable de la gestión operativa de los datos, asegurando la calidad, consistencia y cumplimiento de las políticas definidas por el Data Owner.",
        scope: "Gobierno de Datos",
        category: "Roles",
        status: "APPROVED",
        dataOwner: "CDO",
        dataSteward: "Oficina de Gobierno de Datos",
        sensitivity: "PUBLIC",
      },
    }),
    prisma.glossaryTerm.upsert({
      where: { term: "SLA" },
      update: {},
      create: {
        term: "SLA",
        definition:
          "Acuerdo de Nivel de Servicio (Service Level Agreement). Contrato que define el nivel de servicio esperado entre un proveedor y un cliente.",
        scope: "Operaciones, TI, Comercial",
        category: "Documentos",
        status: "APPROVED",
        dataOwner: "Dirección de Operaciones",
        dataSteward: "Gestión de Servicios",
        sensitivity: "INTERNAL",
        relatedSystems: "Service Desk, CRM",
      },
    }),
  ]);

  // Seed business processes
  const processes = await Promise.all([
    prisma.businessProcess.create({
      data: {
        name: "Alta de Cliente",
        description:
          "Proceso mediante el cual se registra un nuevo Cliente en los sistemas de la organización, verificando su identidad y recopilando la información necesaria para la prestación de servicios.",
        objective: "Registrar correctamente a cada nuevo Cliente cumpliendo la normativa vigente y asegurando la calidad de los datos desde el origen.",
        owner: "María García",
        department: "Comercial",
        status: "ACTIVE",
        inputs: "Solicitud del Cliente, documentación identificativa (NIF/CIF), datos de contacto",
        outputs: "Cliente registrado en CRM y ERP, contrato firmado, comunicación de bienvenida",
        steps: JSON.stringify([
          "Recepción de solicitud del Cliente",
          "Verificación de identidad y documentación",
          "Comprobación de duplicados en el sistema",
          "Registro de datos en CRM",
          "Asignación de código de Cliente en ERP",
          "Generación y firma de contrato",
          "Envío de comunicación de bienvenida",
          "Revisión de calidad de datos por Data Steward",
        ]),
        frequency: "Bajo demanda",
        systems: "CRM, ERP, Plataforma de Firma Digital",
        kpis: "Tiempo medio de alta, Tasa de errores en datos, NPS de onboarding",
      },
    }),
    prisma.businessProcess.create({
      data: {
        name: "Facturación Mensual",
        description:
          "Proceso de generación de Facturas mensuales para todos los Clientes activos en base a los Productos y servicios contratados, siguiendo los SLA establecidos.",
        objective: "Generar y enviar Facturas correctas y puntuales a cada Cliente.",
        owner: "Ana Fernández",
        department: "Finanzas",
        status: "ACTIVE",
        inputs: "Contratos activos, consumos del período, tarifas de Producto vigentes",
        outputs: "Facturas emitidas, asientos contables, informes de facturación",
        steps: JSON.stringify([
          "Cierre del período de consumo",
          "Recopilación de datos de uso por Cliente",
          "Aplicación de tarifas de Producto correspondientes",
          "Generación de borrador de Factura",
          "Validación automática de datos fiscales",
          "Aprobación por el Data Owner del proceso",
          "Emisión y envío de Factura al Cliente",
          "Registro contable y actualización de KPIs",
        ]),
        frequency: "Mensual",
        systems: "ERP, Sistema de Facturación, Contabilidad",
        kpis: "Facturas emitidas a tiempo (%), Errores de facturación (%), Días de cobro medio",
      },
    }),
    prisma.businessProcess.create({
      data: {
        name: "Gestión de Incidencias de Datos",
        description:
          "Proceso para identificar, registrar, analizar y resolver incidencias relacionadas con la calidad de los datos, coordinando las acciones entre el Data Owner, el Data Steward y los equipos técnicos.",
        objective: "Resolver incidencias de calidad de datos en los plazos del SLA definido y prevenir su recurrencia.",
        owner: "Carlos López",
        department: "Gobierno de Datos",
        status: "ACTIVE",
        inputs: "Alerta de calidad, reporte de usuario, detección automática",
        outputs: "Incidencia resuelta, informe de causa raíz, actualización de reglas de calidad",
        steps: JSON.stringify([
          "Detección o reporte de la incidencia",
          "Registro y clasificación por el Data Steward",
          "Análisis de impacto sobre Clientes y Productos afectados",
          "Asignación de prioridad según SLA",
          "Investigación de causa raíz",
          "Implementación de corrección",
          "Validación por el Data Owner",
          "Cierre y documentación de lecciones aprendidas",
          "Actualización de KPIs de calidad de datos",
        ]),
        frequency: "Bajo demanda",
        systems: "Service Desk, Herramienta de Calidad de Datos, BI",
        kpis: "Tiempo medio de resolución, Incidencias recurrentes (%), Impacto en datos corregido (%)",
      },
    }),
  ]);

  // Link glossary terms to processes
  const termMap = new Map(terms.map((t) => [t.term, t.id]));
  const processMap = new Map(processes.map((p) => [p.name, p.id]));

  const links = [
    { process: "Alta de Cliente", terms: ["Cliente", "Data Steward", "KPI"] },
    { process: "Facturación Mensual", terms: ["Factura", "Cliente", "Producto", "SLA", "Data Owner", "KPI"] },
    { process: "Gestión de Incidencias de Datos", terms: ["Data Steward", "Data Owner", "Cliente", "Producto", "SLA", "KPI"] },
  ];

  for (const link of links) {
    const processId = processMap.get(link.process)!;
    for (const termName of link.terms) {
      const termId = termMap.get(termName)!;
      await prisma.processGlossaryTerm.create({
        data: { processId, termId },
      });
    }
  }

  console.log("Seed completed successfully.");
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
