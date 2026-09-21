export type Role = "procesos" | "calidad" | "desempeno" | "administrador";

/** Iconos en public/icons/nav/ (PNG circular con transparencia, generados desde assets/Iconos/). */
export const NAV_ITEMS = [
  { href: "/resumen-general", label: "Resumen General", iconSrc: "/icons/nav/resumen-general.png" },
  { href: "/cmi-estrategico", label: "CMI Estratégico", iconSrc: "/icons/nav/cmi-estrategico.png" },
  { href: "/cmi-procesos", label: "CMI por Procesos", iconSrc: "/icons/nav/cmi-procesos.png" },
  { href: "/informe-procesos", label: "Informe por Procesos", iconSrc: "/icons/nav/informe-procesos.png" },
  { href: "/plan-mejoramiento", label: "Plan de Mejoramiento", iconSrc: "/icons/nav/plan-mejoramiento.png" },
  { href: "/seguimiento-operativo", label: "Seguimiento Operativo", iconSrc: "/icons/nav/seguimiento-operativo.png" },
  { href: "/gestion-om", label: "Gestión OM", iconSrc: "/icons/nav/gestion-om.png" },
] as const;

/**
 * Pantallas visibles para el rol "procesos". Cualquier otra pantalla de NAV_ITEMS
 * (Seguimiento Operativo, Gestión OM) solo la ven administrador, calidad y
 * desempeno. El backend lo refuerza con 403 (require_operational).
 */
const HREFS_PROCESOS: ReadonlySet<string> = new Set([
  "/resumen-general",
  "/cmi-estrategico",
  "/cmi-procesos",
  "/informe-procesos",
  "/plan-mejoramiento",
]);

const ROLES_ACCESO_TOTAL: ReadonlySet<string> = new Set(["administrador", "calidad", "desempeno"]);

export function canAccessHref(role: string | null | undefined, href: string): boolean {
  if (role && ROLES_ACCESO_TOTAL.has(role)) return true;
  return HREFS_PROCESOS.has(href);
}

/** Ítems del menú permitidos para el rol; un rol desconocido o ausente se trata como "procesos". */
export function navItemsForRole(role: string | null | undefined) {
  return NAV_ITEMS.filter((item) => canAccessHref(role, item.href));
}

/** Ruta de dashboard (p. ej. "/gestion-om/x") permitida para el rol. Rutas fuera de NAV_ITEMS no se restringen aquí. */
export function canAccessPath(role: string | null | undefined, pathname: string): boolean {
  const item = NAV_ITEMS.find((i) => pathname === i.href || pathname.startsWith(`${i.href}/`));
  return item ? canAccessHref(role, item.href) : true;
}

/**
 * Reparte n ítems en filas parejas de máximo `maxPerRow` (7 → 4+3, 5 → 3+2, 6 → 3+3),
 * en vez de llenar filas de `maxPerRow` y dejar la última casi vacía.
 */
export function splitIntoRows<T>(items: readonly T[], maxPerRow = 4): T[][] {
  if (items.length === 0) return [];
  const rowCount = Math.ceil(items.length / maxPerRow);
  const perRow = Math.ceil(items.length / rowCount);
  const rows: T[][] = [];
  for (let i = 0; i < items.length; i += perRow) {
    rows.push(items.slice(i, i + perRow));
  }
  return rows;
}

// PDI/Acreditación se eliminó por completo (código, endpoints y esta entrada
// de navegación) — ver docs/tecnico/09-gaps-y-riesgos.md (G-16).
// Diagnóstico es una herramienta interna/técnica, deliberadamente excluida
// de toda navegación de usuario final (nunca debe volver a listarse aquí).
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
  description: string;
  /** undefined = relevante para todos los roles, sin resaltado especial */
  roles?: Role[];
  /** Color distintivo del módulo en el launcher (look de infografía). */
  accent: AccentKey;
  /** Métrica corta opcional mostrada en la tarjeta destacada (ej. "8 procesos"). */
  highlight?: string;
  /** Color hex del resplandor del icono en el launcher; debe coincidir con el color dominante del PNG. */
  pillColor: string;
}

// Metadatos usados solo por el menú de inicio (launcher) — no afecta al Sidebar.
export const NAV_ITEM_META: Record<string, NavItemMeta> = {
  "/resumen-general": {
    description: "Vista consolidada de indicadores institucionales",
    accent: "blue",
    highlight: "Vista general",
    pillColor: "#1F6FB5",
  },
  "/cmi-estrategico": {
    description: "Cuadro de mando integral estratégico",
    roles: ["calidad"],
    accent: "violet",
    highlight: "Estratégico",
    pillColor: "#2563A8",
  },
  "/cmi-procesos": {
    description: "Seguimiento del cuadro de mando por proceso",
    roles: ["procesos"],
    accent: "teal",
    highlight: "Por proceso",
    pillColor: "#3B8FD6",
  },
  "/informe-procesos": {
    description: "Informes detallados por proceso",
    roles: ["procesos"],
    accent: "sky",
    highlight: "Informes",
    pillColor: "#5B3FD1",
  },
  "/plan-mejoramiento": {
    description: "Planes de acción y mejora continua",
    roles: ["calidad"],
    accent: "amber",
    highlight: "Mejora continua",
    pillColor: "#D4188F",
  },
  "/seguimiento-operativo": {
    description: "Monitoreo operativo en tiempo real",
    roles: ["desempeno"],
    accent: "rose",
    highlight: "Tiempo real",
    pillColor: "#F59E0B",
  },
  "/gestion-om": {
    description: "Gestión de oportunidades de mejora",
    roles: ["desempeno"],
    accent: "emerald",
    highlight: "Oportunidades",
    pillColor: "#16A34A",
  },
};

export const BETA_ITEM_META: Record<string, NavItemMeta> = {};
