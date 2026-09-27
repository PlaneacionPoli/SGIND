import type { ResumenLineaProyectoItem } from "@/lib/types";

// Réplica de ganttTimeline() del proyecto de referencia: escala continua
// 2022-01-01 a 2026-12-31, barra coloreada por año de cierre (anio_color,
// ya resuelto en el backend), % centrado, badge gris "Stand by" cuando
// corresponde (sin % en ese caso, igual que el original).
const YEAR_LEGEND: { anio: number; color: string }[] = [
  { anio: 2022, color: "#1a1a1a" },
  { anio: 2023, color: "#FBAF17" },
  { anio: 2024, color: "#1FB2DE" },
  { anio: 2025, color: "#EC0677" },
  { anio: 2026, color: "#A6CE38" },
];

const SCALE_START = 2022;
const SCALE_END = 2027; // fin exclusivo (2026-12-31 ~ inicio de 2027)

function toOffset(anio: number): number {
  return ((anio - SCALE_START) / (SCALE_END - SCALE_START)) * 100;
}

interface ProyectosPmoTimelineProps {
  items: ResumenLineaProyectoItem[];
}

export function ProyectosPmoTimeline({ items }: ProyectosPmoTimelineProps) {
  if (!items.length) {
    return (
      <div className="flex h-32 items-center justify-center text-sm text-slate-500">
        Sin datos de cronograma para mostrar.
      </div>
    );
  }

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-3 text-xs font-semibold text-slate-600">
        {YEAR_LEGEND.map((y) => (
          <span key={y.anio} className="inline-flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: y.color }} />
            {y.anio}
          </span>
        ))}
      </div>

      <div className="relative mb-2 hidden text-[11px] font-semibold text-slate-400 sm:flex">
        {YEAR_LEGEND.map((y) => (
          <span key={y.anio} style={{ position: "absolute", left: `${toOffset(y.anio)}%` }}>
            {y.anio}
          </span>
        ))}
      </div>

      <div className="space-y-2 pt-4">
        {items.map((item) => {
          const left = toOffset(item.anio_inicio);
          const right = toOffset(item.anio_fin + 1);
          const width = Math.max(right - left, 3);
          const barColor = item.anio_color ?? "#64748B";
          return (
            <div key={item.id}>
              <div className="mb-1 truncate text-sm text-slate-700" title={item.nombre}>
                {item.nombre}
              </div>
              <div className="relative h-6 overflow-hidden rounded border border-slate-200 bg-slate-100">
                <div
                  className="absolute flex h-full items-center justify-center rounded-sm"
                  style={{ left: `${left}%`, width: `${width}%`, backgroundColor: barColor }}
                >
                  {!item.stand_by && (
                    <span className="px-1 text-xs font-bold text-white">
                      {Math.round(item.cumplimiento)}%
                    </span>
                  )}
                </div>
                {item.stand_by && (
                  <span className="absolute right-1.5 top-1/2 -translate-y-1/2 whitespace-nowrap rounded-full bg-slate-500 px-2 py-0.5 text-[10px] font-bold text-white">
                    Stand by
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
