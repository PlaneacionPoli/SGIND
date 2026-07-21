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

// Ocultas temporalmente del menú principal y del sidebar (pedido explícito).
// Las rutas siguen activas — solo no aparecen en la navegación. Para
// reactivarlas, mover la entrada de vuelta a NAV_ITEMS/BETA_ITEMS.
// { href: "/plan-mejoramiento", label: "Plan de Mejoramiento", icon: "◐" },
// { href: "/seguimiento-operativo", label: "Seguimiento Operativo", icon: "◧" },
// { href: "/gestion-om", label: "Gestión OM", icon: "◈" },
// { href: "/pdi-acreditacion", label: "PDI Acreditación" },
// { href: "/diagnostico", label: "Diagnóstico" },

export const NAV_ITEMS = [
  { href: "/resumen-general", label: "Resumen General", icon: "◫" },
  { href: "/cmi-estrategico", label: "CMI Estratégico", icon: "⌂" },
  { href: "/cmi-procesos", label: "CMI por Procesos", icon: "◷" },
  { href: "/informe-procesos", label: "Informe por Procesos", icon: "◯" },
] as const;

export const BETA_ITEMS: ReadonlyArray<{ href: string; label: string }> = [];

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
  /** Color hex sólido para el menú de inicio en formato "línea de tiempo". */
  pillColor: string;
}

// Metadatos usados solo por el menú de inicio (launcher) — no afecta al Sidebar.
export const NAV_ITEM_META: Record<string, NavItemMeta> = {
  "/resumen-general": {
    Icon: LayoutDashboard,
    description: "Vista consolidada de indicadores institucionales",
    accent: "blue",
    highlight: "Vista general",
    pillColor: "#0B5D75",
  },
  "/cmi-estrategico": {
    Icon: Target,
    description: "Cuadro de mando integral estratégico",
    roles: ["calidad"],
    accent: "violet",
    highlight: "Estratégico",
    pillColor: "#0E7A81",
  },
  "/cmi-procesos": {
    Icon: Workflow,
    description: "Seguimiento del cuadro de mando por proceso",
    roles: ["procesos"],
    accent: "teal",
    highlight: "Por proceso",
    pillColor: "#10967D",
  },
  "/informe-procesos": {
    Icon: FileText,
    description: "Informes detallados por proceso",
    roles: ["procesos"],
    accent: "sky",
    highlight: "Informes",
    pillColor: "#14B489",
  },
  "/plan-mejoramiento": {
    Icon: TrendingUp,
    description: "Planes de acción y mejora continua",
    roles: ["calidad"],
    accent: "amber",
    highlight: "Mejora continua",
    pillColor: "#D97706",
  },
  "/seguimiento-operativo": {
    Icon: Activity,
    description: "Monitoreo operativo en tiempo real",
    roles: ["desempeno"],
    accent: "rose",
    highlight: "Tiempo real",
    pillColor: "#E11D48",
  },
  "/gestion-om": {
    Icon: ClipboardList,
    description: "Gestión de oportunidades de mejora",
    roles: ["desempeno"],
    accent: "emerald",
    highlight: "Oportunidades",
    pillColor: "#059669",
  },
};

export const BETA_ITEM_META: Record<string, NavItemMeta> = {
  "/pdi-acreditacion": {
    Icon: Award,
    description: "Plan de desarrollo institucional para acreditación",
    accent: "indigo",
    pillColor: "#4338CA",
  },
  "/diagnostico": {
    Icon: Search,
    description: "Diagnóstico institucional",
    accent: "slate",
    pillColor: "#475569",
  },
};
