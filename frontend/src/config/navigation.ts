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

export interface NavItemMeta {
  Icon: LucideIcon;
  description: string;
  /** undefined = relevante para todos los roles, sin resaltado especial */
  roles?: Role[];
}

// Metadatos usados solo por el menú de inicio (launcher) — no afecta al Sidebar.
export const NAV_ITEM_META: Record<string, NavItemMeta> = {
  "/resumen-general": {
    Icon: LayoutDashboard,
    description: "Vista consolidada de indicadores institucionales",
  },
  "/cmi-estrategico": {
    Icon: Target,
    description: "Cuadro de mando integral estratégico",
    roles: ["calidad"],
  },
  "/cmi-procesos": {
    Icon: Workflow,
    description: "Seguimiento del cuadro de mando por proceso",
    roles: ["procesos"],
  },
  "/informe-procesos": {
    Icon: FileText,
    description: "Informes detallados por proceso",
    roles: ["procesos"],
  },
  "/plan-mejoramiento": {
    Icon: TrendingUp,
    description: "Planes de acción y mejora continua",
    roles: ["calidad"],
  },
  "/seguimiento-operativo": {
    Icon: Activity,
    description: "Monitoreo operativo en tiempo real",
    roles: ["desempeno"],
  },
  "/gestion-om": {
    Icon: ClipboardList,
    description: "Gestión de oportunidades de mejora",
    roles: ["desempeno"],
  },
};

export const BETA_ITEM_META: Record<string, NavItemMeta> = {
  "/pdi-acreditacion": {
    Icon: Award,
    description: "Plan de desarrollo institucional para acreditación",
  },
  "/diagnostico": {
    Icon: Search,
    description: "Diagnóstico institucional",
  },
};
