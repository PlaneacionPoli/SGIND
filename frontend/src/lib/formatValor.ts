/**
 * Formatea un valor numérico de Meta o Ejecución según el signo y decimales del indicador.
 * Replica la lógica de _formatear_valor_por_signo en streamlit_app/utils/formatting.py
 */
export function fmtValorSigno(
  valor: number | string | null | undefined,
  signo: string | null | undefined,
  decimales?: number | null,
): string {
  if (valor == null) return "—";

  const num = typeof valor === "number" ? valor : parseFloat(String(valor));
  if (isNaN(num)) return String(valor) || "—";

  const s = (signo ?? "").trim();
  const dec = decimales != null && !isNaN(Number(decimales)) ? Math.max(0, Math.floor(Number(decimales))) : 0;

  if (s === "Sin reporte") return "Pendiente";
  if (s === "Linea Base") return "Linea Base";

  if (s === "ENT") {
    return num === 0 ? "0" : Math.round(num).toLocaleString("es-CO");
  }

  if (s === "%" || s === "kWh") {
    if (dec > 0) return `${num.toFixed(dec).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}${s}`;
    return `${Math.round(num).toLocaleString("es-CO")}${s}`;
  }

  if (s === "$") {
    // Cifras monetarias siempre en millones de pesos en todo el tablero.
    const enPesosCompletos = Math.abs(num) >= 1_000_000;
    const millones = enPesosCompletos ? num / 1_000_000 : num;
    const decMillones = dec > 0 ? dec : enPesosCompletos ? 1 : 0;
    const formatted = decMillones > 0 ? millones.toFixed(decMillones) : Math.round(millones).toString();
    const parts = formatted.split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return `$${parts.join(",")} M`;
  }

  if (s === "DEC") {
    if (dec > 0) return num.toFixed(dec).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return Math.round(num).toLocaleString("es-CO");
  }

  const su = s.toUpperCase();
  if (su === "NO APLICA" || su === "SIN REPORTE" || su === "NA") {
    if (dec > 0) return num.toFixed(dec);
    return Math.round(num).toLocaleString("es-CO");
  }

  if (s === "m3" || s === "Kg" || s === "tCO2e") {
    return `${Math.round(num).toLocaleString("es-CO")} ${s}`;
  }

  // Default: con sufijo
  if (dec > 0) return `${num.toFixed(dec)} ${s}`.trim();
  return `${Math.round(num).toLocaleString("es-CO")}${s ? ` ${s}` : ""}`.trim();
}

/** Extrae los campos de signo y decimales de un indicador genérico. */
export function getSignoMeta(ind: Record<string, unknown>): { signo: string; dec: number } {
  const signo = String(ind["Meta_Signo"] ?? ind["MetaS"] ?? ind["meta_signo"] ?? "%").trim();
  const dec = Number(ind["Decimales_Meta"] ?? ind["DecMeta"] ?? ind["dec_meta"] ?? 0);
  return { signo, dec: isNaN(dec) ? 0 : dec };
}

/**
 * Meta y Ejecución siempre comparten unidad de medida — cumplimiento_pct se calcula
 * como Ejecucion/Meta, lo cual solo tiene sentido si ambas usan el mismo signo. La
 * columna Ejecucion_s/EjecS del origen suele venir vacía o con "%" de relleno del ETL
 * (ver legacy-reference/scripts/etl/escritura.py), así que el signo de Meta es la
 * fuente confiable para formatear ambos valores.
 */
export function getSignoEjec(ind: Record<string, unknown>): { signo: string; dec: number } {
  return getSignoMeta(ind);
}

/** Formatea Meta usando los campos de signo del indicador. */
export function fmtMeta(ind: Record<string, unknown>): string {
  const { signo, dec } = getSignoMeta(ind);
  return fmtValorSigno(ind["Meta"] as number | null | undefined, signo, dec);
}

/** Formatea Ejecución con el mismo signo/decimales que Meta (misma unidad de medida). */
export function fmtEjecucion(ind: Record<string, unknown>): string {
  const { signo, dec } = getSignoMeta(ind);
  return fmtValorSigno(ind["Ejecucion"] as number | null | undefined, signo, dec);
}
