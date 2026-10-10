export const MESES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

export const MESES_CORTO = MESES.map((m) => m.slice(0, 3));

export const corteNombre = (anio: number, mes: number) => `${MESES[mes - 1]} ${anio}`;

/** Paleta del módulo: un color por significado, el mismo en todos los gráficos y tablas. */
export const COLOR = {
  reportado: "#10b981", // emerald-500
  pendiente: "#f59e0b", // amber-500
  noAplica: "#cbd5e1", // slate-300
  critico: "#f43f5e", // rose-500
  marca: "#1a2b4a", // poli-navy
  acento: "#2563eb", // poli-blue
  rejilla: "#e2e8f0", // slate-200
  texto: "#64748b", // slate-500
} as const;

/** Estilos de estado de reporte: fondo suave + texto oscuro (legible en cualquier fondo). */
export const ESTADO_STYLE: Record<string, { chip: string; dot: string; color: string }> = {
  Reportado: { chip: "bg-emerald-50 text-emerald-800 ring-emerald-200", dot: "bg-emerald-500", color: COLOR.reportado },
  Pendiente: { chip: "bg-amber-50 text-amber-800 ring-amber-200", dot: "bg-amber-500", color: COLOR.pendiente },
  "No aplica": { chip: "bg-slate-100 text-slate-600 ring-slate-200", dot: "bg-slate-400", color: COLOR.noAplica },
};

/** Tramos del mapa de calor (de peor a mejor). Se usan también en la leyenda. */
export const TRAMOS_CALOR = [
  { min: 0, max: 50, bg: "#f43f5e", fg: "#ffffff", label: "< 50 %" },
  { min: 50, max: 80, bg: "#fb923c", fg: "#431407", label: "50–79 %" },
  { min: 80, max: 100, bg: "#fcd34d", fg: "#451a03", label: "80–99 %" },
  { min: 100, max: 101, bg: "#10b981", fg: "#ffffff", label: "100 %" },
] as const;

export function tramoCalor(pct: number) {
  return TRAMOS_CALOR.find((t) => pct >= t.min && pct < t.max) ?? TRAMOS_CALOR[0];
}

/** Texto y color de un porcentaje de cumplimiento (para cifras y etiquetas). */
export function tonoCumplimiento(pct: number | null): { text: string; bar: string; label: string } {
  if (pct === null) return { text: "text-slate-500", bar: "bg-slate-300", label: "Sin exigibles" };
  if (pct >= 100) return { text: "text-emerald-700", bar: "bg-emerald-500", label: "Al día" };
  if (pct >= 80) return { text: "text-amber-700", bar: "bg-amber-400", label: "En curso" };
  return { text: "text-rose-700", bar: "bg-rose-500", label: "Atrasado" };
}

export function errorMessage(err: unknown): string {
  const e = err as { response?: { data?: { detail?: unknown } }; message?: string };
  const detail = e?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  return e?.message ?? "Error inesperado";
}
