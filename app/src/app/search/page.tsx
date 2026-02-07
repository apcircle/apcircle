"use client";

import { useState } from "react";
import { Search as SearchIcon, BookOpen, GitBranch } from "lucide-react";
import StatusBadge from "@/components/StatusBadge";
import SensitivityBadge from "@/components/SensitivityBadge";
import Link from "next/link";

interface SearchResult {
  type: "term" | "process";
  id: string;
  title: string;
  description: string;
  status: string;
  extra: Record<string, string | null>;
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setSearched(true);

    const [termsRes, processesRes] = await Promise.all([
      fetch(`/api/glossary?search=${encodeURIComponent(query)}`).then((r) =>
        r.json()
      ),
      fetch(`/api/processes?search=${encodeURIComponent(query)}`).then((r) =>
        r.json()
      ),
    ]);

    const termResults: SearchResult[] = termsRes.map(
      (t: Record<string, string | null>) => ({
        type: "term" as const,
        id: t.id,
        title: t.term,
        description: t.definition,
        status: t.status,
        extra: {
          category: t.category,
          dataOwner: t.dataOwner,
          sensitivity: t.sensitivity,
        },
      })
    );

    const processResults: SearchResult[] = processesRes.map(
      (p: Record<string, string | null>) => ({
        type: "process" as const,
        id: p.id,
        title: p.name,
        description: p.description,
        status: p.status,
        extra: {
          department: p.department,
          owner: p.owner,
        },
      })
    );

    setResults([...termResults, ...processResults]);
    setLoading(false);
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Busqueda Global</h1>
        <p className="text-gray-500 mt-1">
          Buscar en el glosario y los procesos de negocio
        </p>
      </div>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="mb-8">
        <div className="relative">
          <SearchIcon
            size={20}
            className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
          />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Buscar terminos, procesos, definiciones..."
            className="w-full pl-12 pr-32 py-3.5 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm"
          />
          <button
            type="submit"
            className="absolute right-2 top-1/2 -translate-y-1/2 bg-blue-700 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-800 transition-colors"
          >
            Buscar
          </button>
        </div>
      </form>

      {/* Results */}
      {loading && (
        <div className="text-center py-12">
          <div className="animate-pulse text-gray-400">Buscando...</div>
        </div>
      )}

      {searched && !loading && results.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-400">
            No se encontraron resultados para &quot;{query}&quot;
          </p>
        </div>
      )}

      {results.length > 0 && (
        <div className="space-y-3">
          <p className="text-sm text-gray-500 mb-4">
            {results.length} resultado{results.length !== 1 ? "s" : ""}{" "}
            encontrado{results.length !== 1 ? "s" : ""}
          </p>
          {results.map((result) => (
            <Link
              key={`${result.type}-${result.id}`}
              href={
                result.type === "term"
                  ? "/glossary"
                  : "/processes"
              }
              className="block bg-white rounded-xl border border-gray-200 p-4 hover:border-gray-300 hover:shadow-sm transition-all"
            >
              <div className="flex items-start gap-3">
                <div
                  className={`p-2 rounded-lg ${
                    result.type === "term"
                      ? "bg-blue-50"
                      : "bg-purple-50"
                  }`}
                >
                  {result.type === "term" ? (
                    <BookOpen
                      size={16}
                      className="text-blue-600"
                    />
                  ) : (
                    <GitBranch
                      size={16}
                      className="text-purple-600"
                    />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-semibold text-gray-900">
                      {result.title}
                    </h3>
                    <StatusBadge status={result.status} />
                    {result.extra.sensitivity && (
                      <SensitivityBadge
                        sensitivity={result.extra.sensitivity}
                      />
                    )}
                  </div>
                  <p className="text-sm text-gray-600 line-clamp-2">
                    {result.description}
                  </p>
                  <div className="flex gap-4 mt-2 text-xs text-gray-400">
                    {result.type === "term" && result.extra.category && (
                      <span>Categoria: {result.extra.category}</span>
                    )}
                    {result.extra.dataOwner && (
                      <span>Data Owner: {result.extra.dataOwner}</span>
                    )}
                    {result.extra.department && (
                      <span>Dept: {result.extra.department}</span>
                    )}
                    {result.extra.owner && (
                      <span>Responsable: {result.extra.owner}</span>
                    )}
                  </div>
                </div>
                <span
                  className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                    result.type === "term"
                      ? "bg-blue-50 text-blue-700"
                      : "bg-purple-50 text-purple-700"
                  }`}
                >
                  {result.type === "term" ? "Glosario" : "Proceso"}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
