"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpen,
  GitBranch,
  LayoutDashboard,
  Search,
  HelpCircle,
} from "lucide-react";

const nav = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/glossary", label: "Glosario", icon: BookOpen },
  { href: "/processes", label: "Procesos", icon: GitBranch },
  { href: "/search", label: "Buscar", icon: Search },
  { href: "/onboarding", label: "Onboarding", icon: HelpCircle },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col shrink-0">
      {/* Brand */}
      <div className="px-6 py-5 border-b border-gray-200">
        <h1 className="text-lg font-bold text-blue-800">Gobierno de Datos</h1>
        <p className="text-xs text-gray-500 mt-0.5">Glosario &amp; Procesos</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {nav.map(({ href, label, icon: Icon }) => {
          const active =
            href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                active
                  ? "bg-blue-50 text-blue-800"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              }`}
            >
              <Icon size={18} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-6 py-4 border-t border-gray-200">
        <p className="text-xs text-gray-400">
          v1.0 — Data Governance Platform
        </p>
      </div>
    </aside>
  );
}
