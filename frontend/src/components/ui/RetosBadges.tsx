import { TrendingUp, Target, CheckCircle2 } from "lucide-react";
import type { ResumenLineaRetos } from "@/lib/types";

interface RetosBadgesProps {
  retos: ResumenLineaRetos;
  color: string;
}

// Cada caja usa su propio color de acento (línea / #FBAF17 / #A6CE38) en
// vez de un navy uniforme, para diferenciarlas visualmente.
export function RetosBadges({ retos, color }: RetosBadgesProps) {
  const badges = [
    { Icon: TrendingUp, iconColor: color, value: retos.avance_real, label: "Avance Real" },
    { Icon: Target, iconColor: "#FBAF17", value: retos.avance_esperado, label: "Avance Esperado" },
    { Icon: CheckCircle2, iconColor: "#A6CE38", value: retos.cumplimiento, label: "Cumplimiento" },
  ];

  return (
    <div className="space-y-3">
      <div className="flex gap-1.5">
        {badges.map((b) => (
          <div key={b.label} className="flex flex-1 overflow-hidden rounded-lg shadow-sm">
            <div
              className="flex w-9 shrink-0 items-center justify-center"
              style={{ backgroundColor: `${b.iconColor}33` }}
            >
              <b.Icon size={16} color={b.iconColor} strokeWidth={2} />
            </div>
            <div
              className="flex flex-1 flex-col items-center justify-center px-1 py-2"
              style={{ backgroundColor: b.iconColor }}
            >
              <div className="text-base font-black leading-none text-white">
                {Math.round(b.value)}%
              </div>
              <div className="mt-1 text-center text-[9px] font-bold uppercase leading-tight tracking-wide text-white">
                {b.label}
              </div>
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
