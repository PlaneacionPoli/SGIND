import type { ResumenLineaRetos } from "@/lib/types";

interface RetosBadgesProps {
  retos: ResumenLineaRetos;
  color: string;
}

export function RetosBadges({ retos, color }: RetosBadgesProps) {
  const badges = [
    { label: "Avance Real", value: `${retos.avance_real.toFixed(0)}%` },
    { label: "Avance Esperado", value: `${retos.avance_esperado.toFixed(0)}%` },
    { label: "Cumplimiento", value: `${retos.cumplimiento.toFixed(0)}%` },
  ];

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-3 gap-2">
        {badges.map((b) => (
          <div
            key={b.label}
            className="rounded-lg px-2 py-3 text-center text-white shadow-sm"
            style={{ backgroundColor: color }}
          >
            <div className="text-lg font-black leading-none">{b.value}</div>
            <div className="mt-1 text-[10px] font-semibold uppercase tracking-wide opacity-90">
              {b.label}
            </div>
          </div>
        ))}
      </div>
      <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-center shadow-sm">
        <div className="text-2xl font-black text-slate-800">{retos.n_areas}</div>
        <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
          # Áreas con retos
        </div>
      </div>
    </div>
  );
}
