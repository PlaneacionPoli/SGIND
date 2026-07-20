/**
 * Design tokens centralizados para uso en código JS/TS.
 * Fuente única para colores en gráficos Plotly y Recharts.
 * Los valores DEBEN coincidir con tailwind.config.ts y globals.css.
 */

// ─── Marca Poli ──────────────────────────────────────────────────────────────
export const POLI = {
  navy:      "#1a2b4a",
  navy700:   "#243554",
  navy50:    "#f0f3f8",
  blue:      "#2563eb",
  blueDark:  "#1d4ed8",
  blue50:    "#eff6ff",
  gold:      "#c9a227",
  gold50:    "#fef9e7",
} as const;

// ─── Semáforo (fuente única — §3.3 PROJECT_RULES) ────────────────────────────
export const SEMAFORO = {
  peligro:         "#ef4444",
  peligroBg:       "#fef2f2",
  alerta:          "#f59e0b",
  alertaBg:        "#fffbeb",
  cumplimiento:    "#22c55e",
  cumplimientoBg:  "#f0fdf4",
  sobre:           "#3b82f6",
  sobreBg:         "#eff6ff",
} as const;

export type NivelSemaforo = "Peligro" | "Alerta" | "Cumplimiento" | "Sobrecumplimiento";

export const SEMAFORO_COLOR: Record<NivelSemaforo, string> = {
  Peligro:          SEMAFORO.peligro,
  Alerta:           SEMAFORO.alerta,
  Cumplimiento:     SEMAFORO.cumplimiento,
  Sobrecumplimiento:SEMAFORO.sobre,
};

export const SEMAFORO_BG: Record<NivelSemaforo, string> = {
  Peligro:          SEMAFORO.peligroBg,
  Alerta:           SEMAFORO.alertaBg,
  Cumplimiento:     SEMAFORO.cumplimientoBg,
  Sobrecumplimiento:SEMAFORO.sobreBg,
};

// ─── Colores de líneas estratégicas ──────────────────────────────────────────
export const LINEA_COLORS = [
  "#ef4444",  // rojo
  "#2563eb",  // azul Poli
  "#22c55e",  // verde
  "#f59e0b",  // ámbar
  "#8b5cf6",  // violeta
  "#06b6d4",  // cyan
] as const;

// ─── Neutros ─────────────────────────────────────────────────────────────────
export const NEUTRAL = {
  bg:       "#f8fafc",  // --background
  surface:  "#ffffff",
  border:   "#e2e8f0",
  muted:    "#f1f5f9",
  mutedFg:  "#64748b",
  fg:       "#0f172a",
} as const;

// ─── Tema Plotly ─────────────────────────────────────────────────────────────
export const PLOTLY_LAYOUT_BASE = {
  font:       { family: "Inter, system-ui, sans-serif", color: NEUTRAL.fg },
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor:  "rgba(0,0,0,0)",
  margin:     { t: 24, r: 16, b: 40, l: 40 },
  hoverlabel: {
    bgcolor:    POLI.navy,
    bordercolor:POLI.navy,
    font:       { color: "#ffffff", size: 12 },
  },
  xaxis: { gridcolor: NEUTRAL.border, linecolor: NEUTRAL.border, tickfont: { size: 11 } },
  yaxis: { gridcolor: NEUTRAL.border, linecolor: NEUTRAL.border, tickfont: { size: 11 } },
} as const;

// ─── Helpers ─────────────────────────────────────────────────────────────────

/** Devuelve el color hex del semáforo dado un nivel string flexible. */
export function getSemaforoColor(nivel: string): string {
  const map: Record<string, string> = {
    peligro:           SEMAFORO.peligro,
    alerta:            SEMAFORO.alerta,
    cumplimiento:      SEMAFORO.cumplimiento,
    sobrecumplimiento: SEMAFORO.sobre,
  };
  return map[nivel.toLowerCase()] ?? NEUTRAL.mutedFg;
}

/** Devuelve el color de fondo del semáforo dado un nivel string flexible. */
export function getSemaforoBg(nivel: string): string {
  const map: Record<string, string> = {
    peligro:           SEMAFORO.peligroBg,
    alerta:            SEMAFORO.alertaBg,
    cumplimiento:      SEMAFORO.cumplimientoBg,
    sobrecumplimiento: SEMAFORO.sobreBg,
  };
  return map[nivel.toLowerCase()] ?? NEUTRAL.muted;
}
