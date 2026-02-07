"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  BookOpen,
  GitBranch,
  CheckCircle,
  Clock,
  BarChart3,
  ArrowRight,
} from "lucide-react";

interface Stats {
  totalTerms: number;
  approvedTerms: number;
  draftTerms: number;
  totalProcesses: number;
  activeProcesses: number;
  categories: { category: string | null; _count: number }[];
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/stats")
      .then((r) => r.json())
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-pulse text-gray-400">Cargando...</div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">
          Vista general del Glosario de Negocio y Procesos
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-blue-50 rounded-lg">
              <BookOpen size={20} className="text-blue-600" />
            </div>
            <span className="text-sm font-medium text-gray-500">
              Total Terminos
            </span>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {stats?.totalTerms ?? 0}
          </p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-green-50 rounded-lg">
              <CheckCircle size={20} className="text-green-600" />
            </div>
            <span className="text-sm font-medium text-gray-500">
              Aprobados
            </span>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {stats?.approvedTerms ?? 0}
          </p>
          {stats && stats.totalTerms > 0 && (
            <p className="text-xs text-gray-400 mt-1">
              {Math.round((stats.approvedTerms / stats.totalTerms) * 100)}% del
              total
            </p>
          )}
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-yellow-50 rounded-lg">
              <Clock size={20} className="text-yellow-600" />
            </div>
            <span className="text-sm font-medium text-gray-500">
              En Borrador
            </span>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {stats?.draftTerms ?? 0}
          </p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-purple-50 rounded-lg">
              <GitBranch size={20} className="text-purple-600" />
            </div>
            <span className="text-sm font-medium text-gray-500">Procesos</span>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {stats?.totalProcesses ?? 0}
          </p>
          <p className="text-xs text-gray-400 mt-1">
            {stats?.activeProcesses ?? 0} activos
          </p>
        </div>
      </div>

      {/* Categories + Quick Links */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Categories */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 size={18} className="text-gray-400" />
            <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
              Categorias del Glosario
            </h2>
          </div>
          {stats?.categories && stats.categories.length > 0 ? (
            <div className="space-y-3">
              {stats.categories.map((cat) => (
                <div
                  key={cat.category}
                  className="flex items-center justify-between"
                >
                  <span className="text-sm text-gray-700">
                    {cat.category || "Sin categoria"}
                  </span>
                  <span className="text-sm font-semibold text-gray-900">
                    {cat._count}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400">
              No hay categorias registradas
            </p>
          )}
        </div>

        {/* Quick Links */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-4">
            Accesos Rapidos
          </h2>
          <div className="space-y-3">
            <Link
              href="/glossary"
              className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors group"
            >
              <div className="flex items-center gap-3">
                <BookOpen size={18} className="text-blue-600" />
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    Glosario de Terminos
                  </p>
                  <p className="text-xs text-gray-500">
                    Gestionar definiciones y gobierno de datos
                  </p>
                </div>
              </div>
              <ArrowRight
                size={16}
                className="text-gray-300 group-hover:text-blue-600 transition-colors"
              />
            </Link>
            <Link
              href="/processes"
              className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors group"
            >
              <div className="flex items-center gap-3">
                <GitBranch size={18} className="text-purple-600" />
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    Procesos de Negocio
                  </p>
                  <p className="text-xs text-gray-500">
                    Consultar y gestionar procesos
                  </p>
                </div>
              </div>
              <ArrowRight
                size={16}
                className="text-gray-300 group-hover:text-purple-600 transition-colors"
              />
            </Link>
            <Link
              href="/onboarding"
              className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors group"
            >
              <div className="flex items-center gap-3">
                <CheckCircle size={18} className="text-green-600" />
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    Guia de Onboarding
                  </p>
                  <p className="text-xs text-gray-500">
                    Introduccion al gobierno de datos
                  </p>
                </div>
              </div>
              <ArrowRight
                size={16}
                className="text-gray-300 group-hover:text-green-600 transition-colors"
              />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
