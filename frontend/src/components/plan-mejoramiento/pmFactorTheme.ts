import {
  Award,
  FlaskConical,
  GraduationCap,
  Globe,
  HeartHandshake,
  HeartPulse,
  Landmark,
  Leaf,
  Presentation,
  RefreshCw,
  Scale,
  Users,
  type LucideIcon,
} from "lucide-react";

/**
 * Identidad visual de los 12 factores del modelo CNA — Plan de Mejoramiento.
 *
 * No replica los íconos fotográficos del legacy (assets/CNA/1..12.jpeg, ver
 * Sistema_Indicadores_Poli/streamlit_app/utils/cna_icons.py) por decisión de
 * diseño (no copiar visualmente Streamlit). En su lugar usa el mismo lenguaje
 * visual del resto de SGING: íconos Lucide + una paleta extendida de la
 * institucional `STRATEGIC_PALETTE` (cmiChartColors.ts) — un color e ícono
 * temático fijo por factor, reutilizado en gráficos, badges y modales.
 */

export const FACTOR_NAMES: Record<number, string> = {
  1: "Identidad institucional",
  2: "Gobierno institucional y transparencia",
  3: "Desarrollo, gestión y sostenibilidad institucional",
  4: "Mejoramiento continuo y autorregulación",
  5: "Estructura y procesos académicos",
  6: "Aportes de la investigación, la innovación y la creación",
  7: "Impacto social",
  8: "Visibilidad nacional e internacional",
  9: "Bienestar institucional",
  10: "Comunidad de profesores",
  11: "Comunidad de estudiantes",
  12: "Comunidad de egresados",
};

export const FACTOR_COLORS: Record<number, string> = {
  1: "#0F385A", // navy (brand)
  2: "#4C6EF5", // indigo — gobierno/confianza
  3: "#2F9E44", // verde — sostenibilidad
  4: "#F08C00", // naranja — mejora continua
  5: "#1FB2DE", // azul (brand) — académico
  6: "#7048E8", // violeta — investigación/innovación
  7: "#E64980", // rosa — impacto social
  8: "#12B886", // teal — visibilidad/alcance global
  9: "#FA5252", // coral — bienestar
  10: "#FBAF17", // dorado (brand) — profesores
  11: "#A6CE38", // lima (brand) — estudiantes
  12: "#495057", // grafito — egresados
};

export const FACTOR_ICONS: Record<number, LucideIcon> = {
  1: Landmark,
  2: Scale,
  3: Leaf,
  4: RefreshCw,
  5: GraduationCap,
  6: FlaskConical,
  7: HeartHandshake,
  8: Globe,
  9: HeartPulse,
  10: Presentation,
  11: Users,
  12: Award,
};

const FACTOR_LABEL_RE = /Factor\s+(\d+)/i;

/** "Factor 3. Desarrollo..." -> 3 — para endpoints que solo devuelven el
 * label completo del factor, no su número por separado. */
export function parseFactorNum(label: string | null | undefined): number | null {
  const match = label ? FACTOR_LABEL_RE.exec(label) : null;
  return match ? Number(match[1]) : null;
}

const DEFAULT_COLOR = "#64748B";

export function getFactorColor(factorNum: number | null | undefined): string {
  if (factorNum == null) return DEFAULT_COLOR;
  return FACTOR_COLORS[factorNum] ?? DEFAULT_COLOR;
}

export function getFactorIcon(factorNum: number | null | undefined): LucideIcon {
  return (factorNum != null && FACTOR_ICONS[factorNum]) || Landmark;
}
