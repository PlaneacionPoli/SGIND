import type { LucideIcon } from "lucide-react";
import { CalendarClock, CheckCircle2, Clock } from "lucide-react";

export interface ProyectoDetalleRow {
  linea: string;
  id: string;
  nombre: string;
  cumplimiento: number;
  estado: string;
  nivel: string;
}

export interface RetoDetalleRow {
  linea: string;
  cumplimiento: number;
  nivel: string;
}

interface DetailTablesProps {
  vista: string;
  rows?: ProyectoDetalleRow[] | RetoDetalleRow[];
  lineColors?: Record<string, string>;
}

const ESTADO_STYLE: Record<string, { bg: string; fg: string; icon: LucideIcon }> = {
  Cerrado: { bg: "#DCFCE7", fg: "#166534", icon: CheckCircle2 },
  "En ejecución": { bg: "#FEF3C7", fg: "#92400E", icon: Clock },
  default: { bg: "#F1F5F9", fg: "#475569", icon: CalendarClock },
};

const NIVEL_COLORS: Record<string, string> = {
  Sobrecumplimiento: "#173D66",
  Cumplimiento: "#16A34A",
  Alerta: "#D97706",
  Peligro: "#D32F2F",
};

export function DetailTables({ vista, rows, lineColors }: DetailTablesProps) {
  if (!rows?.length) return null;

  if (vista === "proyectos") {
    const proyectos = rows as ProyectoDetalleRow[];
    return (
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-left text-[11px] uppercase tracking-wide text-slate-500">
                <th className="px-4 py-3">Línea estratégica</th>
                <th className="px-4 py-3">Proyecto institucional</th>
                <th className="px-4 py-3">Cumplimiento</th>
                <th className="px-4 py-3 text-right">Estado</th>
              </tr>
            </thead>
            <tbody>
              {proyectos.map((item) => {
                const color = lineColors?.[item.linea] ?? "#64748B";
                const est = ESTADO_STYLE[item.estado] ?? ESTADO_STYLE.default;
                const EstIcon = est.icon;
                const pct = Math.max(0, Math.min(100, item.cumplimiento));
                return (
                  <tr key={item.id} className="border-b border-slate-50 last:border-0">
                    <td className="px-4 py-2.5">
                      <span
                        className="inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-[11px] font-medium"
                        style={{ backgroundColor: `${color}1A`, color, border: `1px solid ${color}40` }}
                      >
                        <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: color }} />
                        {item.linea}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-slate-800">{item.nombre}</td>
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-3">
                        <span className="w-12 text-xs font-semibold text-slate-700">{item.cumplimiento}%</span>
                        <div className="h-2 w-40 overflow-hidden rounded-full bg-slate-100">
                          <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: color }} />
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-2.5 text-right">
                      <span
                        className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium"
                        style={{ backgroundColor: est.bg, color: est.fg }}
                      >
                        <EstIcon size={12} />
                        {item.estado}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  if (vista === "retos") {
    const retos = rows as RetoDetalleRow[];
    return (
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-700">
          Cumplimiento por línea estratégica
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-base">
            <thead>
              <tr className="border-b border-slate-100 text-left text-sm uppercase tracking-wide text-slate-500">
                <th className="px-4 py-2">Línea</th>
                <th className="px-4 py-2">Cumplimiento</th>
                <th className="px-4 py-2">Nivel</th>
              </tr>
            </thead>
            <tbody>
              {retos.map((item) => (
                <tr key={item.linea} className="border-b border-slate-50 last:border-0">
                  <td className="px-4 py-2 text-slate-800">{item.linea}</td>
                  <td className="px-4 py-2 font-semibold text-slate-700">{item.cumplimiento}%</td>
                  <td className="px-4 py-2">
                    <span
                      className="rounded-full px-3 py-0.5 text-sm font-semibold"
                      style={{
                        backgroundColor: `${NIVEL_COLORS[item.nivel] ?? "#6B7280"}22`,
                        color: NIVEL_COLORS[item.nivel] ?? "#475569",
                      }}
                    >
                      {item.nivel}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return null;
}
