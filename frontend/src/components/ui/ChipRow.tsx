import type { LucideIcon } from "lucide-react";
import { AlertTriangle, BarChart3, CalendarClock, CheckCircle2, Clock, FolderKanban, OctagonAlert, TrendingUp } from "lucide-react";

export interface ChipItem {
  value: number | string;
  label: string;
  color: string;
}

interface ChipRowProps {
  chips: ChipItem[];
}

/** Icono según el estado del chip (vista Proyectos); null si no aplica. */
function iconForLabel(label: string): LucideIcon | null {
  const l = label.toLowerCase();
  if (l.includes("sobrecumplimiento")) return TrendingUp;
  if (l.includes("alerta")) return AlertTriangle;
  if (l.includes("peligro")) return OctagonAlert;
  if (l.includes("total proyectos")) return FolderKanban;
  if (l.includes("cerrado") || l.startsWith("cumplimiento")) return CheckCircle2;
  if (l.includes("ejecuci")) return Clock;
  if (l.includes("planeaci")) return CalendarClock;
  return null;
}

export function ChipRow({ chips }: ChipRowProps) {
  if (!chips.length) return null;
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-[repeat(auto-fit,minmax(180px,1fr))]">
      {chips.map((chip) => {
        const Icon = iconForLabel(chip.label) ?? BarChart3;
        return (
          <div
            key={chip.label}
            className="flex items-center justify-between gap-3 rounded-xl px-4 py-3.5"
            style={{
              background: `linear-gradient(180deg, ${chip.color}14 0%, ${chip.color}05 100%)`,
              border: `1px solid ${chip.color}30`,
              boxShadow: `0 2px 8px ${chip.color}1A`,
            }}
          >
            <div className="min-w-0">
              <div
                className="truncate text-[11px] font-semibold uppercase tracking-wide"
                style={{ color: chip.color }}
              >
                {chip.label}
              </div>
              <div className="mt-1 text-[1.85rem] font-extrabold leading-none" style={{ color: chip.color }}>
                {chip.value}
              </div>
            </div>
            {Icon && (
              <div
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg"
                style={{ background: `${chip.color}1F`, color: chip.color }}
              >
                <Icon size={20} strokeWidth={2} />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
