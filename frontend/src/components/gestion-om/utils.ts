import type { OMFila } from "@/lib/types";

export type EstadoOM = "sin_om" | "en_gestion" | "cerrada";
export type Pestana = "pendientes" | "en_gestion" | "cerradas" | "todos";
export type ColumnaOM = "prioridad" | "id" | "indicador" | "proceso" | "cumplimiento" | "avance";
export type Orden = { por: ColumnaOM; dir: "asc" | "desc" };

export const TIPOS_ACCION = ["OM Kawak", "Reto Plan Anual", "Proyecto Institucional", "Otro"] as const;

/** Placeholder contextual por tipo de acción (paridad con streamlit_app/pages/gestion_om.py). */
export const PLACEHOLDERS_TIPO_ACCION: Record<string, string> = {
  "OM Kawak": "N° OM Kawak",
  "Reto Plan Anual": "Nombre del reto",
  "Proyecto Institucional": "Nombre del proyecto",
  Otro: "Descripción de la acción",
};

export const ESTADO_OM_STYLE: Record<EstadoOM, { etiqueta: string; chip: string; color: string }> = {
  sin_om: { etiqueta: "Sin OM", chip: "bg-rose-50 text-rose-800 ring-rose-200", color: "#f43f5e" },
  en_gestion: { etiqueta: "En gestión", chip: "bg-blue-50 text-blue-800 ring-blue-200", color: "#2563eb" },
  cerrada: { etiqueta: "Cerrada", chip: "bg-emerald-50 text-emerald-800 ring-emerald-200", color: "#10b981" },
};

export const CATEGORIA_STYLE: Record<string, { chip: string; dot: string }> = {
  Peligro: { chip: "bg-rose-50 text-rose-800 ring-rose-200", dot: "bg-rose-500" },
  Alerta: { chip: "bg-amber-50 text-amber-800 ring-amber-200", dot: "bg-amber-500" },
};

/** Un registro activo es «en gestión»; uno cerrado conserva su fila pero ya no cuenta como activo. */
export function estadoOM(f: Pick<OMFila, "tiene_om" | "om_id">): EstadoOM {
  if (f.tiene_om === 1) return "en_gestion";
  return f.om_id != null ? "cerrada" : "sin_om";
}

export function contarPorEstado(filas: OMFila[]): Record<EstadoOM, number> {
  const c: Record<EstadoOM, number> = { sin_om: 0, en_gestion: 0, cerrada: 0 };
  for (const f of filas) c[estadoOM(f)] += 1;
  return c;
}

/** Cifras legibles: `10049277970` → «10.049,3 M»; `-732.08` → «-732,08». */
export function formatNumero(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "—";
  const abs = Math.abs(n);
  const fmt = (v: number, max: number) => v.toLocaleString("es-CO", { maximumFractionDigits: max });
  if (abs >= 1e6) return `${fmt(n / 1e6, 1)} M`;
  if (abs >= 1e4) return fmt(n, 0);
  return fmt(n, 2);
}

const quitaTildes = (s: string) => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();

const COINCIDE_PESTANA: Record<Pestana, (e: EstadoOM) => boolean> = {
  pendientes: (e) => e === "sin_om",
  en_gestion: (e) => e === "en_gestion",
  cerradas: (e) => e === "cerrada",
  todos: () => true,
};

export function filtrarFilas(filas: OMFila[], pestana: Pestana, busqueda: string): OMFila[] {
  const q = quitaTildes(busqueda.trim());
  return filas.filter((f) => {
    if (!COINCIDE_PESTANA[pestana](estadoOM(f))) return false;
    if (!q) return true;
    return quitaTildes(`${f.id} ${f.indicador} ${f.proceso} ${f.subproceso} ${f.numero_om}`).includes(q);
  });
}

const RANGO_ESTADO: Record<EstadoOM, number> = { sin_om: 0, en_gestion: 1, cerrada: 2 };

/** Los nulos van siempre al final, sea cual sea la dirección. */
function comparar(a: number | string | null, b: number | string | null, dir: 1 | -1): number {
  if (a == null && b == null) return 0;
  if (a == null) return 1;
  if (b == null) return -1;
  if (typeof a === "number" && typeof b === "number") return (a - b) * dir;
  return String(a).localeCompare(String(b), "es", { numeric: true }) * dir;
}

export function ordenarFilas(filas: OMFila[], orden: Orden, agruparPorProceso = false): OMFila[] {
  const dir = orden.dir === "asc" ? 1 : -1;
  const valor = (f: OMFila): number | string | null => {
    switch (orden.por) {
      case "id":
        return Number.isNaN(Number(f.id)) ? f.id : Number(f.id);
      case "indicador":
        return f.indicador;
      case "proceso":
        return f.proceso;
      case "cumplimiento":
        return f.cumplimiento_pct;
      case "avance":
        return f.avance_om;
      default:
        return RANGO_ESTADO[estadoOM(f)];
    }
  };
  return [...filas].sort((a, b) => {
    if (agruparPorProceso) {
      const g = comparar(a.proceso, b.proceso, 1);
      if (g !== 0) return g;
    }
    const c = comparar(valor(a), valor(b), dir);
    if (c !== 0) return c;
    // Prioridad: a igual estado, primero el menor cumplimiento (más lejos de la meta).
    if (orden.por === "prioridad") return comparar(a.cumplimiento_pct, b.cumplimiento_pct, 1);
    return comparar(Number(a.id), Number(b.id), 1);
  });
}

/** Validación del formulario de registro. Devuelve el mensaje de error o `null`. */
export function validarRegistro(tipo: string, numeroOm: string): string | null {
  if (tipo === "OM Kawak" && !numeroOm.trim()) return "Indica el N° de la OM en Kawak.";
  if (tipo === "OM Kawak" && !/\d/.test(numeroOm)) return "El N° de OM debe incluir al menos un número (por ejemplo 440).";
  return null;
}
