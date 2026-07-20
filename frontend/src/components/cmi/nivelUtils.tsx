const NIVEL_STYLES: Record<string, { text: string; bg: string }> = {
  Peligro: { text: "#B71C1C", bg: "#FEE2E2" },
  Alerta: { text: "#B45309", bg: "#FEF3C7" },
  Cumplimiento: { text: "#166534", bg: "#DCFCE7" },
  Sobrecumplimiento: { text: "#1D4ED8", bg: "#DBEAFE" },
  "Pendiente de reporte": { text: "#475569", bg: "#F1F5F9" },
};

export function NivelBadge({ nivel }: { nivel?: string }) {
  const n = nivel ?? "Pendiente de reporte";
  const style = NIVEL_STYLES[n] ?? { text: "#334155", bg: "#F8FAFC" };
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-bold"
      style={{ color: style.text, backgroundColor: style.bg }}
    >
      <span className="h-2 w-2 rounded-full" style={{ backgroundColor: style.text }} />
      {n}
    </span>
  );
}

export function fmtPct(val?: number | null, digits = 1) {
  if (val == null || Number.isNaN(val)) return "—";
  return `${Number(val).toFixed(digits)}%`;
}

export function fmtNum(val?: number | null, digits = 1) {
  if (val == null || Number.isNaN(val)) return "—";
  return Number(val).toFixed(digits);
}
