export const STRATEGIC_PALETTE = ["#FBAF17", "#42F2F2", "#EC0677", "#1FB2DE", "#A6CE38", "#0F385A"];

export const NIVEL_COLORS: Record<string, string> = {
  Sobrecumplimiento: "#6699FF",
  Cumplimiento: "#43A047",
  Alerta: "#FBAF17",
  Peligro: "#D32F2F",
  "Pendiente de reporte": "#9E9E9E",
};

export function paletteColor(index: number): string {
  return STRATEGIC_PALETTE[index % STRATEGIC_PALETTE.length];
}
