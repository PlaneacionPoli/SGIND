// Mapeo de líneas estratégicas del PDI para navegación (landing "flor" +
// hojas de línea). Slugs normalizan igual que norm_key() en el backend
// (guiones -> espacios), así que sirven directamente como {key} de la ruta
// /dashboard/resumen-linea/{key}. Debe reflejar STRATEGIC_LINE_DEFS en
// backend/app/domain/resumen_builders.py.
export interface StrategicLineDef {
  slug: string;
  label: string;
  icon: string;
  color: string;
}

export const STRATEGIC_LINES: StrategicLineDef[] = [
  { slug: "expansion", label: "Expansión", icon: "rocket", color: "#FBAF17" },
  {
    slug: "transformacion-organizacional",
    label: "Transformación Organizacional",
    icon: "chart",
    color: "#0891b2",
  },
  { slug: "calidad", label: "Calidad", icon: "medal", color: "#EC0677" },
  { slug: "experiencia", label: "Experiencia", icon: "bulb", color: "#1FB2DE" },
  { slug: "sostenibilidad", label: "Sostenibilidad", icon: "leaf", color: "#A6CE38" },
  {
    slug: "educacion-para-toda-la-vida",
    label: "Educación para toda la vida",
    icon: "graduation",
    color: "#0F385A",
  },
];

export function findStrategicLine(slug: string): StrategicLineDef | undefined {
  return STRATEGIC_LINES.find((l) => l.slug === slug);
}
