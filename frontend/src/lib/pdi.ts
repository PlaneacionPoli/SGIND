"use client";

import { useEffect } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";

/** Marco de referencia versionado (backend: app/domain/marcos.py). */
export interface Marco {
  tipo: "PDI" | "CNA";
  version_id: string;
  nombre: string;
  descripcion: string;
  anio_datos_desde: number;
  anio_datos_hasta: number | null;
  estado: "activo" | "cerrado";
  orden: number;
  imagen: string | null;
  /** false = la versión aún no tiene datos cargados; el módulo muestra un aviso. */
  datos_disponibles: boolean;
}

export async function fetchMarcos(tipo: "PDI" | "CNA" = "PDI"): Promise<Marco[]> {
  const { data } = await api.get<Marco[]>("/marcos", { params: { tipo } });
  return data;
}

/** Módulos que exigen elegir PDI antes de mostrarse. */
export const MODULOS_CON_PDI: ReadonlySet<string> = new Set([
  "/resumen-general",
  "/cmi-estrategico",
  "/cmi-procesos",
]);

/** Ciclo al que están fijas las vistas por línea (consolidado-por-linea, ficha de línea). */
export const PDI_VISTAS_POR_LINEA = "PDI-2022-2026";

export const SELECCION_PDI_PATH = "/seleccion-pdi";

export function seleccionPdiHref(destino: string): string {
  return `${SELECCION_PDI_PATH}?destino=${encodeURIComponent(destino)}`;
}

/** Destino permitido del selector (evita redirecciones abiertas). */
export function destinoValido(destino: string | null): string | null {
  return destino && MODULOS_CON_PDI.has(destino) ? destino : null;
}

export function moduloHref(destino: string, versionId: string): string {
  return `${destino}?pdi=${encodeURIComponent(versionId)}`;
}

/**
 * PDI elegido para el módulo actual, tomado de `?pdi=`. Si falta, redirige a
 * la pantalla de selección y devuelve null (la página no debe renderizar
 * datos hasta tener PDI). Requiere estar dentro de <Suspense>.
 */
export function usePdiSeleccionado(): string | null {
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();
  const pdi = searchParams.get("pdi");

  useEffect(() => {
    if (!pdi) {
      const base = Array.from(MODULOS_CON_PDI).find(
        (m) => pathname === m || pathname.startsWith(`${m}/`)
      );
      router.replace(seleccionPdiHref(base ?? pathname));
    }
  }, [pdi, pathname, router]);

  return pdi;
}
