"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Plus,
  Search,
  Edit2,
  Trash2,
  ChevronDown,
  ChevronRight,
  Filter,
  Clock,
  Users,
  Layers,
} from "lucide-react";
import StatusBadge from "@/components/StatusBadge";
import GlossaryTooltip from "@/components/GlossaryTooltip";
import Modal from "@/components/Modal";

interface GlossaryTermData {
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
}

interface BusinessProcess {
  id: string;
  name: string;
  description: string;
  objective: string | null;
  owner: string | null;
  department: string | null;
  status: string;
  inputs: string | null;
  outputs: string | null;
  steps: string | null;
  frequency: string | null;
  systems: string | null;
  kpis: string | null;
  glossaryTerms: { term: GlossaryTermData }[];
  children: { id: string; name: string }[];
}

const emptyForm = {
  name: "",
  description: "",
  objective: "",
  owner: "",
  department: "",
  status: "DRAFT",
  inputs: "",
  outputs: "",
  steps: "",
  frequency: "",
  systems: "",
  kpis: "",
  glossaryTermIds: [] as string[],
};

export default function ProcessesPage() {
  const [processes, setProcesses] = useState<BusinessProcess[]>([]);
  const [allTerms, setAllTerms] = useState<GlossaryTermData[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterDept, setFilterDept] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [editingProcess, setEditingProcess] = useState<BusinessProcess | null>(
    null
  );
  const [form, setForm] = useState(emptyForm);

  const fetchProcesses = useCallback(() => {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (filterStatus) params.set("status", filterStatus);
    if (filterDept) params.set("department", filterDept);

    fetch(`/api/processes?${params}`)
      .then((r) => r.json())
      .then(setProcesses)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [search, filterStatus, filterDept]);

  useEffect(() => {
    fetchProcesses();
    fetch("/api/glossary")
      .then((r) => r.json())
      .then(setAllTerms)
      .catch(console.error);
  }, [fetchProcesses]);

  const departments = [
    ...new Set(processes.map((p) => p.department).filter(Boolean)),
  ];

  function openCreate() {
    setEditingProcess(null);
    setForm(emptyForm);
    setModalOpen(true);
  }

  function openEdit(process: BusinessProcess) {
    setEditingProcess(process);
    setForm({
      name: process.name,
      description: process.description,
      objective: process.objective || "",
      owner: process.owner || "",
      department: process.department || "",
      status: process.status,
      inputs: process.inputs || "",
      outputs: process.outputs || "",
      steps: process.steps || "",
      frequency: process.frequency || "",
      systems: process.systems || "",
      kpis: process.kpis || "",
      glossaryTermIds: process.glossaryTerms.map((gt) => gt.term.id),
    });
    setModalOpen(true);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const url = editingProcess
      ? `/api/processes/${editingProcess.id}`
      : "/api/processes";
    const method = editingProcess ? "PUT" : "POST";

    await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });

    setModalOpen(false);
    fetchProcesses();
  }

  async function handleDelete(id: string) {
    if (!confirm("Estas seguro de eliminar este proceso?")) return;
    await fetch(`/api/processes/${id}`, { method: "DELETE" });
    fetchProcesses();
  }

  function parseSteps(steps: string | null): string[] {
    if (!steps) return [];
    try {
      return JSON.parse(steps);
    } catch {
      return steps.split("\n").filter(Boolean);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-pulse text-gray-400">
          Cargando procesos...
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Procesos de Negocio
          </h1>
          <p className="text-gray-500 mt-1">
            Catalogo de procesos con terminos del glosario vinculados
          </p>
        </div>
        <button
          onClick={openCreate}
          className="flex items-center gap-2 bg-purple-700 text-white px-4 py-2.5 rounded-lg hover:bg-purple-800 transition-colors text-sm font-medium"
        >
          <Plus size={16} />
          Nuevo Proceso
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
              placeholder="Buscar procesos..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-sm ${
              showFilters
                ? "border-purple-300 bg-purple-50 text-purple-700"
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
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="">Todos los estados</option>
              <option value="DRAFT">Borrador</option>
              <option value="ACTIVE">Activo</option>
              <option value="UNDER_REVIEW">En revision</option>
              <option value="ARCHIVED">Archivado</option>
            </select>
            <select
              value={filterDept}
              onChange={(e) => setFilterDept(e.target.value)}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="">Todos los departamentos</option>
              {departments.map((d) => (
                <option key={d} value={d!}>
                  {d}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Process Cards */}
      <div className="space-y-4">
        {processes.map((process) => {
          const isExpanded = expandedId === process.id;
          const steps = parseSteps(process.steps);
          const linkedTerms = process.glossaryTerms.map((gt) => gt.term);

          return (
            <div
              key={process.id}
              className="bg-white rounded-xl border border-gray-200 overflow-hidden"
            >
              {/* Card Header */}
              <div
                className="px-6 py-4 flex items-center justify-between cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() =>
                  setExpandedId(isExpanded ? null : process.id)
                }
              >
                <div className="flex items-center gap-3">
                  {isExpanded ? (
                    <ChevronDown size={18} className="text-gray-400" />
                  ) : (
                    <ChevronRight size={18} className="text-gray-400" />
                  )}
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold text-gray-900">
                        {process.name}
                      </h3>
                      <StatusBadge status={process.status} />
                    </div>
                    <div className="flex items-center gap-4 mt-1 text-xs text-gray-500">
                      {process.department && (
                        <span className="flex items-center gap-1">
                          <Layers size={12} />
                          {process.department}
                        </span>
                      )}
                      {process.owner && (
                        <span className="flex items-center gap-1">
                          <Users size={12} />
                          {process.owner}
                        </span>
                      )}
                      {process.frequency && (
                        <span className="flex items-center gap-1">
                          <Clock size={12} />
                          {process.frequency}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div
                  className="flex items-center gap-2"
                  onClick={(e) => e.stopPropagation()}
                >
                  {linkedTerms.length > 0 && (
                    <span className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded-full font-medium">
                      {linkedTerms.length} termino
                      {linkedTerms.length !== 1 ? "s" : ""}
                    </span>
                  )}
                  <button
                    onClick={() => openEdit(process)}
                    className="p-1.5 text-gray-400 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
                    title="Editar"
                  >
                    <Edit2 size={14} />
                  </button>
                  <button
                    onClick={() => handleDelete(process.id)}
                    className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    title="Eliminar"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>

              {/* Expanded Detail */}
              {isExpanded && (
                <div className="px-6 pb-6 border-t border-gray-100">
                  <div className="pt-4 space-y-4">
                    {/* Description with glossary highlighting */}
                    <div>
                      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                        Descripcion
                      </h4>
                      <div className="text-sm text-gray-700 leading-relaxed">
                        <GlossaryTooltip
                          text={process.description}
                          terms={linkedTerms}
                        />
                      </div>
                    </div>

                    {process.objective && (
                      <div>
                        <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                          Objetivo
                        </h4>
                        <div className="text-sm text-gray-700 leading-relaxed">
                          <GlossaryTooltip
                            text={process.objective}
                            terms={linkedTerms}
                          />
                        </div>
                      </div>
                    )}

                    {/* Steps */}
                    {steps.length > 0 && (
                      <div>
                        <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                          Pasos del Proceso
                        </h4>
                        <ol className="space-y-2">
                          {steps.map((step, i) => (
                            <li
                              key={i}
                              className="flex items-start gap-3 text-sm text-gray-700"
                            >
                              <span className="flex-shrink-0 w-6 h-6 bg-purple-100 text-purple-700 rounded-full flex items-center justify-center text-xs font-semibold">
                                {i + 1}
                              </span>
                              <div className="pt-0.5">
                                <GlossaryTooltip
                                  text={step}
                                  terms={linkedTerms}
                                />
                              </div>
                            </li>
                          ))}
                        </ol>
                      </div>
                    )}

                    {/* Inputs / Outputs */}
                    <div className="grid grid-cols-2 gap-4">
                      {process.inputs && (
                        <div>
                          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                            Entradas
                          </h4>
                          <div className="text-sm text-gray-700">
                            <GlossaryTooltip
                              text={process.inputs}
                              terms={linkedTerms}
                            />
                          </div>
                        </div>
                      )}
                      {process.outputs && (
                        <div>
                          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                            Salidas
                          </h4>
                          <div className="text-sm text-gray-700">
                            <GlossaryTooltip
                              text={process.outputs}
                              terms={linkedTerms}
                            />
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Systems & KPIs */}
                    <div className="grid grid-cols-2 gap-4">
                      {process.systems && (
                        <div>
                          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                            Sistemas
                          </h4>
                          <p className="text-sm text-gray-700">
                            {process.systems}
                          </p>
                        </div>
                      )}
                      {process.kpis && (
                        <div>
                          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                            KPIs
                          </h4>
                          <div className="text-sm text-gray-700">
                            <GlossaryTooltip
                              text={process.kpis}
                              terms={linkedTerms}
                            />
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Linked Terms */}
                    {linkedTerms.length > 0 && (
                      <div>
                        <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                          Terminos del Glosario Vinculados
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {linkedTerms.map((term) => (
                            <span
                              key={term.id}
                              className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200"
                            >
                              {term.term}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}

        {processes.length === 0 && (
          <div className="bg-white rounded-xl border border-gray-200 px-6 py-12 text-center">
            <p className="text-gray-400">No se encontraron procesos</p>
          </div>
        )}
      </div>

      {/* Create / Edit Modal */}
      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingProcess ? "Editar Proceso" : "Nuevo Proceso"}
        size="xl"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nombre *
              </label>
              <input
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Departamento
              </label>
              <input
                value={form.department}
                onChange={(e) =>
                  setForm({ ...form, department: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Descripcion *
            </label>
            <textarea
              required
              rows={3}
              value={form.description}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Objetivo
            </label>
            <textarea
              rows={2}
              value={form.objective}
              onChange={(e) =>
                setForm({ ...form, objective: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Responsable
              </label>
              <input
                value={form.owner}
                onChange={(e) => setForm({ ...form, owner: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Estado
              </label>
              <select
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="DRAFT">Borrador</option>
                <option value="ACTIVE">Activo</option>
                <option value="UNDER_REVIEW">En revision</option>
                <option value="ARCHIVED">Archivado</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Frecuencia
              </label>
              <input
                value={form.frequency}
                onChange={(e) =>
                  setForm({ ...form, frequency: e.target.value })
                }
                placeholder="Ej: Diaria, Mensual..."
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Entradas
              </label>
              <textarea
                rows={2}
                value={form.inputs}
                onChange={(e) =>
                  setForm({ ...form, inputs: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Salidas
              </label>
              <textarea
                rows={2}
                value={form.outputs}
                onChange={(e) =>
                  setForm({ ...form, outputs: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Pasos (uno por linea)
            </label>
            <textarea
              rows={4}
              value={
                form.steps
                  ? (() => {
                      try {
                        return JSON.parse(form.steps).join("\n");
                      } catch {
                        return form.steps;
                      }
                    })()
                  : ""
              }
              onChange={(e) =>
                setForm({
                  ...form,
                  steps: JSON.stringify(
                    e.target.value
                      .split("\n")
                      .filter((s) => s.trim())
                  ),
                })
              }
              placeholder="Paso 1&#10;Paso 2&#10;Paso 3"
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Sistemas
              </label>
              <input
                value={form.systems}
                onChange={(e) =>
                  setForm({ ...form, systems: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                KPIs
              </label>
              <input
                value={form.kpis}
                onChange={(e) => setForm({ ...form, kpis: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
          </div>

          {/* Link Glossary Terms */}
          <div className="border-t border-gray-100 pt-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Vincular Terminos del Glosario
            </label>
            <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto p-3 border border-gray-200 rounded-lg">
              {allTerms.map((term) => (
                <label
                  key={term.id}
                  className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium cursor-pointer transition-colors ${
                    form.glossaryTermIds.includes(term.id)
                      ? "bg-blue-100 text-blue-800 border border-blue-300"
                      : "bg-gray-50 text-gray-600 border border-gray-200 hover:bg-gray-100"
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={form.glossaryTermIds.includes(term.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setForm({
                          ...form,
                          glossaryTermIds: [
                            ...form.glossaryTermIds,
                            term.id,
                          ],
                        });
                      } else {
                        setForm({
                          ...form,
                          glossaryTermIds: form.glossaryTermIds.filter(
                            (id) => id !== term.id
                          ),
                        });
                      }
                    }}
                    className="sr-only"
                  />
                  {term.term}
                </label>
              ))}
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
              className="px-4 py-2 text-sm font-medium text-white bg-purple-700 hover:bg-purple-800 rounded-lg transition-colors"
            >
              {editingProcess ? "Guardar Cambios" : "Crear Proceso"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
