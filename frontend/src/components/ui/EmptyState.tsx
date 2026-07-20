import { cn } from "@/lib/utils";
import { BarChart3, Filter, SearchX } from "lucide-react";

interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
  variant?: "default" | "filter" | "search";
}

const VARIANTS = {
  default: {
    icon: <BarChart3 className="w-10 h-10 text-slate-300" />,
    title: "Sin datos disponibles",
    description: "No hay información para mostrar en este momento.",
  },
  filter: {
    icon: <Filter className="w-10 h-10 text-slate-300" />,
    title: "Sin resultados",
    description: "No se encontraron registros con los filtros seleccionados.",
  },
  search: {
    icon: <SearchX className="w-10 h-10 text-slate-300" />,
    title: "Sin coincidencias",
    description: "Intenta ajustar los criterios de búsqueda.",
  },
} as const;

export function EmptyState({
  title,
  description,
  icon,
  action,
  className,
  variant = "default",
}: EmptyStateProps) {
  const defaults = VARIANTS[variant];

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-4 py-14 px-6 text-center",
        className
      )}
    >
      <div className="rounded-full bg-slate-50 p-4 border border-slate-100">
        {icon ?? defaults.icon}
      </div>
      <div className="space-y-1 max-w-xs">
        <p className="text-sm font-semibold text-slate-700">{title ?? defaults.title}</p>
        <p className="text-xs text-slate-400">{description ?? defaults.description}</p>
      </div>
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
