"use client";

import { useEffect, useState } from "react";
import {
  BookOpen,
  Shield,
  User,
  Database,
  CheckCircle,
  ArrowRight,
  Users,
} from "lucide-react";
import Link from "next/link";

interface Stats {
  totalTerms: number;
  approvedTerms: number;
  totalProcesses: number;
  activeProcesses: number;
}

export default function OnboardingPage() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    fetch("/api/stats")
      .then((r) => r.json())
      .then(setStats)
      .catch(console.error);
  }, []);

  return (
    <div className="p-8 max-w-4xl mx-auto">
      {/* Hero */}
      <div className="bg-gradient-to-br from-blue-800 to-blue-900 rounded-2xl p-8 text-white mb-8">
        <h1 className="text-3xl font-bold mb-2">
          Bienvenido al Gobierno de Datos
        </h1>
        <p className="text-blue-200 text-lg leading-relaxed max-w-2xl">
          Esta plataforma es el punto central para comprender los terminos de
          negocio, los procesos organizacionales y las responsabilidades en
          torno a nuestros datos.
        </p>
        {stats && (
          <div className="flex gap-6 mt-6">
            <div className="bg-white/10 rounded-lg px-4 py-3">
              <p className="text-2xl font-bold">{stats.totalTerms}</p>
              <p className="text-blue-200 text-sm">Terminos definidos</p>
            </div>
            <div className="bg-white/10 rounded-lg px-4 py-3">
              <p className="text-2xl font-bold">{stats.totalProcesses}</p>
              <p className="text-blue-200 text-sm">Procesos documentados</p>
            </div>
            <div className="bg-white/10 rounded-lg px-4 py-3">
              <p className="text-2xl font-bold">{stats.approvedTerms}</p>
              <p className="text-blue-200 text-sm">Terminos aprobados</p>
            </div>
          </div>
        )}
      </div>

      {/* What is Data Governance */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Que es el Gobierno de Datos?
        </h2>
        <p className="text-sm text-gray-700 leading-relaxed mb-4">
          El Gobierno de Datos es el conjunto de politicas, procesos y
          responsabilidades que aseguran que los datos de la organizacion se
          gestionan de manera correcta, segura y consistente. Incluye definir
          quien es responsable de cada dato, como se debe usar y que reglas de
          calidad debe cumplir.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <Database size={20} className="text-blue-600 mb-2" />
            <h3 className="text-sm font-semibold text-gray-900">Calidad</h3>
            <p className="text-xs text-gray-600 mt-1">
              Asegurar que los datos sean precisos, completos y actualizados
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <Shield size={20} className="text-green-600 mb-2" />
            <h3 className="text-sm font-semibold text-gray-900">Seguridad</h3>
            <p className="text-xs text-gray-600 mt-1">
              Proteger los datos segun su nivel de sensibilidad
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <Users size={20} className="text-purple-600 mb-2" />
            <h3 className="text-sm font-semibold text-gray-900">
              Responsabilidad
            </h3>
            <p className="text-xs text-gray-600 mt-1">
              Definir quien gestiona y es responsable de cada dato
            </p>
          </div>
        </div>
      </div>

      {/* Key Roles */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Roles Clave
        </h2>
        <div className="space-y-4">
          <div className="flex items-start gap-4 p-4 bg-blue-50 rounded-lg">
            <User size={20} className="text-blue-600 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold text-gray-900">
                Data Owner
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Responsable de negocio con autoridad sobre un conjunto de datos.
                Define las politicas de acceso, calidad y uso. Es quien toma
                las decisiones sobre los datos de su ambito.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-4 p-4 bg-green-50 rounded-lg">
            <Shield size={20} className="text-green-600 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold text-gray-900">
                Data Steward
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Responsable de la gestion operativa de los datos. Asegura la
                calidad, consistencia y cumplimiento de las politicas. Es el
                punto de contacto para incidencias de datos.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-4 p-4 bg-purple-50 rounded-lg">
            <Database size={20} className="text-purple-600 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold text-gray-900">
                Data Custodian
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Responsable tecnico del almacenamiento, mantenimiento y
                seguridad de los datos en los sistemas de informacion.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* How to use */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Como usar esta plataforma
        </h2>
        <div className="space-y-4">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-sm font-bold">
              1
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900">
                Consulta el Glosario
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Busca cualquier termino de negocio para ver su definicion
                oficial, alcance, nivel de sensibilidad y quien es responsable
                de ese dato.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 w-8 h-8 bg-purple-100 text-purple-700 rounded-full flex items-center justify-center text-sm font-bold">
              2
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900">
                Explora los Procesos
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Revisa los procesos de negocio documentados. Los terminos del
                glosario aparecen resaltados y puedes hacer clic en ellos para
                ver toda la informacion de gobierno.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 w-8 h-8 bg-green-100 text-green-700 rounded-full flex items-center justify-center text-sm font-bold">
              3
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900">
                Identifica Responsables
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Cada termino tiene asociado un Data Owner, Data Steward y Data
                Custodian. Si tienes una duda o incidencia sobre un dato,
                contacta al responsable correspondiente.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* CTAs */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link
          href="/glossary"
          className="flex items-center justify-between p-5 bg-blue-700 text-white rounded-xl hover:bg-blue-800 transition-colors group"
        >
          <div className="flex items-center gap-3">
            <BookOpen size={20} />
            <div>
              <p className="font-semibold">Ir al Glosario</p>
              <p className="text-blue-200 text-sm">
                Consultar terminos y definiciones
              </p>
            </div>
          </div>
          <ArrowRight
            size={18}
            className="group-hover:translate-x-1 transition-transform"
          />
        </Link>
        <Link
          href="/processes"
          className="flex items-center justify-between p-5 bg-purple-700 text-white rounded-xl hover:bg-purple-800 transition-colors group"
        >
          <div className="flex items-center gap-3">
            <CheckCircle size={20} />
            <div>
              <p className="font-semibold">Ver Procesos</p>
              <p className="text-purple-200 text-sm">
                Explorar los procesos de negocio
              </p>
            </div>
          </div>
          <ArrowRight
            size={18}
            className="group-hover:translate-x-1 transition-transform"
          />
        </Link>
      </div>
    </div>
  );
}
