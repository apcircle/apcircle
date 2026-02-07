"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Plus,
  Search,
  Edit2,
  Trash2,
  User,
  Shield,
  Eye,
  Filter,
} from "lucide-react";
import StatusBadge from "@/components/StatusBadge";
import SensitivityBadge from "@/components/SensitivityBadge";
import Modal from "@/components/Modal";

interface GlossaryTerm {
  id: string;
  term: string;
  definition: string;
  scope: string | null;
  category: string | null;
  status: string;
  dataOwner: string | null;
  dataOwnerEmail: string | null;
  dataSteward: string | null;
  dataStewardEmail: string | null;
  dataCustodian: string | null;
  sensitivity: string;
  qualityRules: string | null;
  relatedSystems: string | null;
  processes: { process: { id: string; name: string } }[];
  createdAt: string;
  updatedAt: string;
}

const emptyForm = {
  term: "",
  definition: "",
  scope: "",
  category: "",
  status: "DRAFT",
  dataOwner: "",
  dataOwnerEmail: "",
  dataSteward: "",
  dataStewardEmail: "",
  dataCustodian: "",
  sensitivity: "INTERNAL",
  qualityRules: "",
  relatedSystems: "",
};

export default function GlossaryPage() {
  const [terms, setTerms] = useState<GlossaryTerm[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterCategory, setFilterCategory] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [showFilters, setShowFilters] = useState(false);

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);
  const [editingTerm, setEditingTerm] = useState<GlossaryTerm | null>(null);
  const [selectedTerm, setSelectedTerm] = useState<GlossaryTerm | null>(null);
  const [form, setForm] = useState(emptyForm);

  const fetchTerms = useCallback(() => {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (filterCategory) params.set("category", filterCategory);
    if (filterStatus) params.set("status", filterStatus);

    fetch(`/api/glossary?${params}`)
      .then((r) => r.json())
      .then(setTerms)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [search, filterCategory, filterStatus]);

  useEffect(() => {
    fetchTerms();
  }, [fetchTerms]);

  const categories = [...new Set(terms.map((t) => t.category).filter(Boolean))];

  function openCreate() {
    setEditingTerm(null);
    setForm(emptyForm);
    setModalOpen(true);
  }

  function openEdit(term: GlossaryTerm) {
    setEditingTerm(term);
    setForm({
      term: term.term,
      definition: term.definition,
      scope: term.scope || "",
      category: term.category || "",
      status: term.status,
      dataOwner: term.dataOwner || "",
      dataOwnerEmail: term.dataOwnerEmail || "",
      dataSteward: term.dataSteward || "",
      dataStewardEmail: term.dataStewardEmail || "",
      dataCustodian: term.dataCustodian || "",
      sensitivity: term.sensitivity,
      qualityRules: term.qualityRules || "",
      relatedSystems: term.relatedSystems || "",
    });
    setModalOpen(true);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const url = editingTerm
      ? `/api/glossary/${editingTerm.id}`
      : "/api/glossary";
    const method = editingTerm ? "PUT" : "POST";

    await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });

    setModalOpen(false);
    fetchTerms();
  }

  async function handleDelete(id: string) {
    if (!confirm("Estas seguro de eliminar este termino?")) return;
    await fetch(`/api/glossary/${id}`, { method: "DELETE" });
    fetchTerms();
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-pulse text-gray-400">Cargando glosario...</div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Glosario de Negocio
          </h1>
          <p className="text-gray-500 mt-1">
            Repositorio de terminos con definiciones y gobierno de datos
          </p>
        </div>
        <button
          onClick={openCreate}
          className="flex items-center gap-2 bg-blue-700 text-white px-4 py-2.5 rounded-lg hover:bg-blue-800 transition-colors text-sm font-medium"
        >
          <Plus size={16} />
          Nuevo Termino
        </button>
      </div>

      {/* Search & Filters */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="flex-1 relative">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
            />
            <input
              type="text"
              placeholder="Buscar terminos..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-sm ${
              showFilters
                ? "border-blue-300 bg-blue-50 text-blue-700"
                : "border-gray-200 text-gray-600 hover:bg-gray-50"
            }`}
          >
            <Filter size={14} />
            Filtros
          </button>
        </div>
        {showFilters && (
          <div className="flex gap-3 mt-3 pt-3 border-t border-gray-100">
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todas las categorias</option>
              {categories.map((c) => (
                <option key={c} value={c!}>
                  {c}
                </option>
              ))}
            </select>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todos los estados</option>
              <option value="DRAFT">Borrador</option>
              <option value="REVIEW">En revision</option>
              <option value="APPROVED">Aprobado</option>
              <option value="DEPRECATED">Obsoleto</option>
            </select>
          </div>
        )}
      </div>

      {/* Terms Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Termino
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Categoria
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Estado
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Data Owner
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Sensibilidad
              </th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Acciones
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {terms.map((term) => (
              <tr
                key={term.id}
                className="hover:bg-gray-50 transition-colors cursor-pointer"
                onClick={() => {
                  setSelectedTerm(term);
                  setDetailOpen(true);
                }}
              >
                <td className="px-6 py-4">
                  <p className="text-sm font-medium text-gray-900">
                    {term.term}
                  </p>
                  <p className="text-xs text-gray-500 line-clamp-1 max-w-xs">
                    {term.definition}
                  </p>
                </td>
                <td className="px-6 py-4">
                  <span className="text-sm text-gray-600">
                    {term.category || "—"}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <StatusBadge status={term.status} />
                </td>
                <td className="px-6 py-4">
                  <span className="text-sm text-gray-600">
                    {term.dataOwner || "—"}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <SensitivityBadge sensitivity={term.sensitivity} />
                </td>
                <td className="px-6 py-4 text-right">
                  <div
                    className="flex items-center justify-end gap-2"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <button
                      onClick={() => openEdit(term)}
                      className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      title="Editar"
                    >
                      <Edit2 size={14} />
                    </button>
                    <button
                      onClick={() => handleDelete(term.id)}
                      className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Eliminar"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {terms.length === 0 && (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center">
                  <p className="text-gray-400">No se encontraron terminos</p>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Create / Edit Modal */}
      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingTerm ? "Editar Termino" : "Nuevo Termino"}
        size="xl"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Termino *
              </label>
              <input
                required
                value={form.term}
                onChange={(e) => setForm({ ...form, term: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Categoria
              </label>
              <input
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
                placeholder="Ej: Entidades, Documentos, Metricas..."
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Definicion *
            </label>
            <textarea
              required
              rows={3}
              value={form.definition}
              onChange={(e) =>
                setForm({ ...form, definition: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Alcance
            </label>
            <input
              value={form.scope}
              onChange={(e) => setForm({ ...form, scope: e.target.value })}
              placeholder="Ej: Toda la organizacion, Finanzas..."
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Estado
              </label>
              <select
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="DRAFT">Borrador</option>
                <option value="REVIEW">En revision</option>
                <option value="APPROVED">Aprobado</option>
                <option value="DEPRECATED">Obsoleto</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Sensibilidad
              </label>
              <select
                value={form.sensitivity}
                onChange={(e) =>
                  setForm({ ...form, sensitivity: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="PUBLIC">Publico</option>
                <option value="INTERNAL">Interno</option>
                <option value="CONFIDENTIAL">Confidencial</option>
                <option value="RESTRICTED">Restringido</option>
              </select>
            </div>
          </div>

          {/* Governance Section */}
          <div className="border-t border-gray-100 pt-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">
              Gobierno de Datos
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Data Owner
                </label>
                <input
                  value={form.dataOwner}
                  onChange={(e) =>
                    setForm({ ...form, dataOwner: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email Data Owner
                </label>
                <input
                  type="email"
                  value={form.dataOwnerEmail}
                  onChange={(e) =>
                    setForm({ ...form, dataOwnerEmail: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Data Steward
                </label>
                <input
                  value={form.dataSteward}
                  onChange={(e) =>
                    setForm({ ...form, dataSteward: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email Data Steward
                </label>
                <input
                  type="email"
                  value={form.dataStewardEmail}
                  onChange={(e) =>
                    setForm({ ...form, dataStewardEmail: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Data Custodian
                </label>
                <input
                  value={form.dataCustodian}
                  onChange={(e) =>
                    setForm({ ...form, dataCustodian: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Quality & Systems */}
          <div className="border-t border-gray-100 pt-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Reglas de Calidad
              </label>
              <textarea
                rows={2}
                value={form.qualityRules}
                onChange={(e) =>
                  setForm({ ...form, qualityRules: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="mt-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Sistemas Relacionados
              </label>
              <input
                value={form.relatedSystems}
                onChange={(e) =>
                  setForm({ ...form, relatedSystems: e.target.value })
                }
                placeholder="Ej: CRM, ERP, BI"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
            <button
              type="button"
              onClick={() => setModalOpen(false)}
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium text-white bg-blue-700 hover:bg-blue-800 rounded-lg transition-colors"
            >
              {editingTerm ? "Guardar Cambios" : "Crear Termino"}
            </button>
          </div>
        </form>
      </Modal>

      {/* Detail Modal */}
      <Modal
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
        title={selectedTerm?.term || ""}
        size="lg"
      >
        {selectedTerm && (
          <div className="space-y-4">
            <div className="flex gap-2">
              <StatusBadge status={selectedTerm.status} />
              <SensitivityBadge sensitivity={selectedTerm.sensitivity} />
              {selectedTerm.category && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
                  {selectedTerm.category}
                </span>
              )}
            </div>

            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                Definicion
              </h4>
              <p className="text-sm text-gray-700 leading-relaxed">
                {selectedTerm.definition}
              </p>
            </div>

            {selectedTerm.scope && (
              <div className="flex items-start gap-2">
                <Eye size={14} className="mt-1 text-gray-400" />
                <div>
                  <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Alcance
                  </h4>
                  <p className="text-sm text-gray-700">{selectedTerm.scope}</p>
                </div>
              </div>
            )}

            {/* Governance */}
            <div className="bg-gray-50 rounded-lg p-4 space-y-3">
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Gobierno de Datos
              </h4>
              {selectedTerm.dataOwner && (
                <div className="flex items-center gap-2 text-sm">
                  <User size={14} className="text-blue-600" />
                  <span className="font-medium text-gray-700">
                    Data Owner:
                  </span>
                  <span className="text-gray-600">
                    {selectedTerm.dataOwner}
                  </span>
                  {selectedTerm.dataOwnerEmail && (
                    <span className="text-gray-400">
                      ({selectedTerm.dataOwnerEmail})
                    </span>
                  )}
                </div>
              )}
              {selectedTerm.dataSteward && (
                <div className="flex items-center gap-2 text-sm">
                  <Shield size={14} className="text-green-600" />
                  <span className="font-medium text-gray-700">
                    Data Steward:
                  </span>
                  <span className="text-gray-600">
                    {selectedTerm.dataSteward}
                  </span>
                  {selectedTerm.dataStewardEmail && (
                    <span className="text-gray-400">
                      ({selectedTerm.dataStewardEmail})
                    </span>
                  )}
                </div>
              )}
              {selectedTerm.dataCustodian && (
                <div className="flex items-center gap-2 text-sm">
                  <User size={14} className="text-purple-600" />
                  <span className="font-medium text-gray-700">
                    Data Custodian:
                  </span>
                  <span className="text-gray-600">
                    {selectedTerm.dataCustodian}
                  </span>
                </div>
              )}
            </div>

            {selectedTerm.qualityRules && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                <h4 className="text-xs font-semibold text-amber-800 uppercase tracking-wide mb-1">
                  Reglas de Calidad
                </h4>
                <p className="text-sm text-amber-700">
                  {selectedTerm.qualityRules}
                </p>
              </div>
            )}

            {selectedTerm.relatedSystems && (
              <div>
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                  Sistemas Relacionados
                </h4>
                <p className="text-sm text-gray-700">
                  {selectedTerm.relatedSystems}
                </p>
              </div>
            )}

            {selectedTerm.processes.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                  Procesos Asociados
                </h4>
                <div className="flex flex-wrap gap-2">
                  {selectedTerm.processes.map((p) => (
                    <span
                      key={p.process.id}
                      className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium bg-purple-50 text-purple-700"
                    >
                      {p.process.name}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
