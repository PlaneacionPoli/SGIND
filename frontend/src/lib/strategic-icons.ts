import { ReactNode } from "react";
import { Award, BookOpen, Cpu, HeartHandshake, Leaf, Shield, Users } from "lucide-react";

export type StrategicIconComponent = (props: {
  size: number;
  style?: React.CSSProperties;
  className?: string;
  strokeWidth?: number;
}) => ReactNode;

// La clave es el `icon` de cada línea (backend STRATEGIC_LINE_DEFS y
// strategic-lines.ts). El glifo sale de los objetivos de cada línea en el PDI
// 2022-2026:
//  - Calidad: calidad institucional y oferta/innovación curricular → sello
//  - Expansión: "crecer con compromiso social" → alianza solidaria
//  - Transformación: arquitectura tecnológica, talento, procesos y datos → chip
//  - Experiencia: experiencia de valor para la comunidad POLI → personas
//  - Sostenibilidad: inclusión, medio ambiente y recursos → hoja
//  - Educación para toda la vida: educación continua, media y para el trabajo → libro
export const STRATEGIC_ICON_MAP: Record<string, StrategicIconComponent> = {
  rocket: HeartHandshake,
  chart: Cpu,
  medal: Award,
  bulb: Users,
  leaf: Leaf,
  graduation: BookOpen,
  shield: Shield,
};
