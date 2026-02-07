"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { User, Shield, Eye, X } from "lucide-react";
import StatusBadge from "./StatusBadge";
import SensitivityBadge from "./SensitivityBadge";

interface GlossaryTermData {
  id: string;
  term: string;
  definition: string;
  scope?: string | null;
  category?: string | null;
  status: string;
  dataOwner?: string | null;
  dataOwnerEmail?: string | null;
  dataSteward?: string | null;
  dataStewardEmail?: string | null;
  dataCustodian?: string | null;
  sensitivity: string;
  qualityRules?: string | null;
  relatedSystems?: string | null;
}

interface GlossaryTooltipProps {
  text: string;
  terms: GlossaryTermData[];
}

export default function GlossaryTooltip({ text, terms }: GlossaryTooltipProps) {
  const [activeTerm, setActiveTerm] = useState<GlossaryTermData | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ top: 0, left: 0 });
  const containerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  const handleClick = useCallback(
    (term: GlossaryTermData, e: React.MouseEvent) => {
      const rect = (e.target as HTMLElement).getBoundingClientRect();
      const containerRect = containerRef.current?.getBoundingClientRect();
      if (containerRect) {
        setTooltipPos({
          top: rect.bottom - containerRect.top + 8,
          left: Math.min(
            rect.left - containerRect.left,
            containerRect.width - 384
          ),
        });
      }
      setActiveTerm(activeTerm?.id === term.id ? null : term);
    },
    [activeTerm]
  );

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (
        tooltipRef.current &&
        !tooltipRef.current.contains(e.target as Node)
      ) {
        setActiveTerm(null);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Build highlighted text
  if (!terms.length) return <span>{text}</span>;

  const sortedTerms = [...terms].sort(
    (a, b) => b.term.length - a.term.length
  );
  const pattern = new RegExp(
    `(${sortedTerms.map((t) => t.term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`,
    "gi"
  );
  const parts = text.split(pattern);

  return (
    <div ref={containerRef} className="relative">
      <span>
        {parts.map((part, i) => {
          const matchedTerm = terms.find(
            (t) => t.term.toLowerCase() === part.toLowerCase()
          );
          if (matchedTerm) {
            return (
              <span
                key={i}
                className="glossary-highlight"
                onClick={(e) => handleClick(matchedTerm, e)}
                title={`Ver definicion: ${matchedTerm.term}`}
              >
                {part}
              </span>
            );
          }
          return <span key={i}>{part}</span>;
        })}
      </span>

      {/* Tooltip card */}
      {activeTerm && (
        <div
          ref={tooltipRef}
          className="absolute z-50 w-96 bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden"
          style={{ top: tooltipPos.top, left: Math.max(0, tooltipPos.left) }}
        >
          {/* Header */}
          <div className="bg-blue-800 text-white px-4 py-3 flex items-center justify-between">
            <div>
              <h4 className="font-semibold text-sm">{activeTerm.term}</h4>
              {activeTerm.category && (
                <span className="text-blue-200 text-xs">
                  {activeTerm.category}
                </span>
              )}
            </div>
            <button
              onClick={() => setActiveTerm(null)}
              className="text-blue-200 hover:text-white"
            >
              <X size={16} />
            </button>
          </div>

          {/* Body */}
          <div className="p-4 space-y-3 text-sm">
            <p className="text-gray-700 leading-relaxed">
              {activeTerm.definition}
            </p>

            <div className="flex gap-2">
              <StatusBadge status={activeTerm.status} />
              <SensitivityBadge sensitivity={activeTerm.sensitivity} />
            </div>

            {activeTerm.scope && (
              <div className="flex items-start gap-2 text-gray-600">
                <Eye size={14} className="mt-0.5 shrink-0 text-gray-400" />
                <span>
                  <strong className="text-gray-700">Alcance:</strong>{" "}
                  {activeTerm.scope}
                </span>
              </div>
            )}

            {/* Governance roles */}
            <div className="border-t border-gray-100 pt-3 space-y-2">
              {activeTerm.dataOwner && (
                <div className="flex items-center gap-2 text-gray-600">
                  <User size={14} className="text-blue-600 shrink-0" />
                  <span>
                    <strong className="text-gray-700">Data Owner:</strong>{" "}
                    {activeTerm.dataOwner}
                    {activeTerm.dataOwnerEmail && (
                      <span className="text-gray-400 ml-1">
                        ({activeTerm.dataOwnerEmail})
                      </span>
                    )}
                  </span>
                </div>
              )}
              {activeTerm.dataSteward && (
                <div className="flex items-center gap-2 text-gray-600">
                  <Shield size={14} className="text-green-600 shrink-0" />
                  <span>
                    <strong className="text-gray-700">Data Steward:</strong>{" "}
                    {activeTerm.dataSteward}
                    {activeTerm.dataStewardEmail && (
                      <span className="text-gray-400 ml-1">
                        ({activeTerm.dataStewardEmail})
                      </span>
                    )}
                  </span>
                </div>
              )}
              {activeTerm.dataCustodian && (
                <div className="flex items-center gap-2 text-gray-600">
                  <User size={14} className="text-purple-600 shrink-0" />
                  <span>
                    <strong className="text-gray-700">Data Custodian:</strong>{" "}
                    {activeTerm.dataCustodian}
                  </span>
                </div>
              )}
            </div>

            {activeTerm.qualityRules && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-2 text-xs text-amber-800">
                <strong>Reglas de calidad:</strong> {activeTerm.qualityRules}
              </div>
            )}

            {activeTerm.relatedSystems && (
              <div className="text-xs text-gray-500">
                <strong>Sistemas:</strong> {activeTerm.relatedSystems}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
