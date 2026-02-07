const colors: Record<string, string> = {
  PUBLIC: "bg-blue-100 text-blue-800",
  INTERNAL: "bg-cyan-100 text-cyan-800",
  CONFIDENTIAL: "bg-orange-100 text-orange-800",
  RESTRICTED: "bg-red-100 text-red-800",
};

const labels: Record<string, string> = {
  PUBLIC: "Publico",
  INTERNAL: "Interno",
  CONFIDENTIAL: "Confidencial",
  RESTRICTED: "Restringido",
};

export default function SensitivityBadge({
  sensitivity,
}: {
  sensitivity: string;
}) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
        colors[sensitivity] || "bg-gray-100 text-gray-700"
      }`}
    >
      {labels[sensitivity] || sensitivity}
    </span>
  );
}
