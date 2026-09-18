import { getFactorColor, getFactorIcon } from "./pmFactorTheme";

interface PmFactorBadgeProps {
  factorNum: number | null;
  /** "pill": ícono + "F{n}" compacto (tablas). "full": ícono + número + nombre (headers/modales). */
  variant?: "pill" | "full";
  className?: string;
}

/** Insignia visual de factor CNA — ícono + color temático fijo por factor,
 * reemplaza el texto plano "F1"/"F2" del diseño anterior. */
export function PmFactorBadge({ factorNum, variant = "pill", className = "" }: PmFactorBadgeProps) {
  const color = getFactorColor(factorNum);
  const Icon = getFactorIcon(factorNum);
  const label = factorNum != null ? `F${factorNum}` : "—";

  if (variant === "full") {
    return (
      <span
        className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-bold text-white ${className}`}
        style={{ backgroundColor: color }}
      >
        <Icon size={13} strokeWidth={2.5} />
        {label}
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[11px] font-bold ${className}`}
      style={{ backgroundColor: `${color}1F`, color }}
    >
      <Icon size={11} strokeWidth={2.5} />
      {label}
    </span>
  );
}
