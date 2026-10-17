import { SEMAFORO_COLOR } from "@/lib/design-tokens";

export const STRATEGIC_PALETTE = ["#FBAF17", "#42F2F2", "#EC0677", "#1FB2DE", "#A6CE38", "#0F385A"];

// Fuente única: lib/design-tokens.ts (antes tenía su propia copia
// desactualizada de la paleta — Oleada 2, ver docs/tecnico/05-reglas-de-negocio.md).
export const NIVEL_COLORS: Record<string, string> = {
  Sobrecumplimiento: SEMAFORO_COLOR.Sobrecumplimiento,
  Cumplimiento: SEMAFORO_COLOR.Cumplimiento,
  Alerta: SEMAFORO_COLOR.Alerta,
  Peligro: SEMAFORO_COLOR.Peligro,
  "Pendiente de reporte": "#9E9E9E",
};

export function paletteColor(index: number): string {
  return STRATEGIC_PALETTE[index % STRATEGIC_PALETTE.length];
}

/** Color de semáforo por cumplimiento (< 80 peligro, < 100 alerta, < 105 cumplimiento). */
export function colorCumplimiento(v: number | null | undefined): string {
  if (v == null) return NIVEL_COLORS["Pendiente de reporte"];
  if (v < 80) return NIVEL_COLORS.Peligro;
  if (v < 100) return NIVEL_COLORS.Alerta;
  return v < 105 ? NIVEL_COLORS.Cumplimiento : NIVEL_COLORS.Sobrecumplimiento;
}
