import {
  Activity,
  Award,
  ClipboardList,
  FileText,
  LayoutDashboard,
  Search,
  Target,
  TrendingUp,
  Workflow,
  type LucideIcon,
} from "lucide-react";

export type Role = "procesos" | "calidad" | "desempeno";

export const NAV_ITEMS = [
  { href: "/resumen-general", label: "Resumen General", icon: "◫" },
  { href: "/cmi-estrategico", label: "CMI Estratégico", icon: "⌂" },
  { href: "/cmi-procesos", label: "CMI por Procesos", icon: "◷" },
  { href: "/informe-procesos", label: "Informe por Procesos", icon: "◯" },
  { href: "/plan-mejoramiento", label: "Plan de Mejoramiento", icon: "◐" },
  { href: "/seguimiento-operativo", label: "Seguimiento Operativo", icon: "◧" },
  { href: "/gestion-om", label: "Gestión OM", icon: "◈" },
] as const;

export const BETA_ITEMS = [
  { href: "/pdi-acreditacion", label: "PDI Acreditación" },
  { href: "/diagnostico", label: "Diagnóstico" },
] as const;

/** Paleta de acento del launcher — claves con clases Tailwind literales en LauncherCard. */
export type AccentKey =
  | "blue"
  | "violet"
  | "teal"
  | "sky"
  | "amber"
  | "rose"
  | "emerald"
  | "indigo"
  | "slate";

export interface NavItemMeta {
  Icon: LucideIcon;
  description: string;
  /** undefined = relevante para todos los roles, sin resaltado especial */
  roles?: Role[];
  /** Color distintivo del módulo en el launcher (look de infografía). */
  accent: AccentKey;
  /** Métrica corta opcional mostrada en la tarjeta destacada (ej. "8 procesos"). */
  highlight?: string;
}

// Metadatos usados solo por el menú de inicio (launcher) — no afecta al Sidebar.
export const NAV_ITEM_META: Record<string, NavItemMeta> = {
  "/resumen-general": {
    Icon: LayoutDashboard,
    description: "Vista consolidada de indicadores institucionales",
    accent: "blue",
    highlight: "Vista general",
  },
  "/cmi-estrategico": {
    Icon: Target,
    description: "Cuadro de mando integral estratégico",
    roles: ["calidad"],
    accent: "violet",
    highlight: "Estratégico",
  },
  "/cmi-procesos": {
    Icon: Workflow,
    description: "Seguimiento del cuadro de mando por proceso",
    roles: ["procesos"],
    accent: "teal",
    highlight: "Por proceso",
  },
  "/informe-procesos": {
    Icon: FileText,
    description: "Informes detallados por proceso",
    roles: ["procesos"],
    accent: "sky",
    highlight: "Informes",
  },
  "/plan-mejoramiento": {
    Icon: TrendingUp,
    description: "Planes de acción y mejora continua",
    roles: ["calidad"],
    accent: "amber",
    highlight: "Mejora continua",
  },
  "/seguimiento-operativo": {
    Icon: Activity,
    description: "Monitoreo operativo en tiempo real",
    roles: ["desempeno"],
    accent: "rose",
    highlight: "Tiempo real",
  },
  "/gestion-om": {
    Icon: ClipboardList,
    description: "Gestión de oportunidades de mejora",
    roles: ["desempeno"],
    accent: "emerald",
    highlight: "Oportunidades",
  },
};

export const BETA_ITEM_META: Record<string, NavItemMeta> = {
  "/pdi-acreditacion": {
    Icon: Award,
    description: "Plan de desarrollo institucional para acreditación",
    accent: "indigo",
  },
  "/diagnostico": {
    Icon: Search,
    description: "Diagnóstico institucional",
    accent: "slate",
  },
};
