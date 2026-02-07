const colors: Record<string, string> = {
  DRAFT: "bg-gray-100 text-gray-700",
  REVIEW: "bg-yellow-100 text-yellow-800",
  APPROVED: "bg-green-100 text-green-800",
  DEPRECATED: "bg-red-100 text-red-700",
  ACTIVE: "bg-green-100 text-green-800",
  UNDER_REVIEW: "bg-yellow-100 text-yellow-800",
  ARCHIVED: "bg-gray-100 text-gray-600",
};

const labels: Record<string, string> = {
  DRAFT: "Borrador",
  REVIEW: "En revision",
  APPROVED: "Aprobado",
  DEPRECATED: "Obsoleto",
  ACTIVE: "Activo",
  UNDER_REVIEW: "En revision",
  ARCHIVED: "Archivado",
};

export default function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
        colors[status] || "bg-gray-100 text-gray-700"
      }`}
    >
      {labels[status] || status}
    </span>
  );
}
