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
    const formatted = dec > 0 ? num.toFixed(dec) : Math.round(num).toString();
    const parts = formatted.split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return `$${parts.join(",")}`;
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

export function getSignoEjec(ind: Record<string, unknown>): { signo: string; dec: number } {
  const signo = String(
    ind["Ejecucion_s"] ?? ind["EjecS"] ?? ind["Ejecucion_Signo"] ?? ind["ejec_signo"] ?? "%",
  ).trim();
  const dec = Number(ind["Decimales_Ejecucion"] ?? ind["DecEjec"] ?? ind["dec_ejec"] ?? 0);
  return { signo, dec: isNaN(dec) ? 0 : dec };
}

/** Formatea Meta usando los campos de signo del indicador. */
export function fmtMeta(ind: Record<string, unknown>): string {
  const { signo, dec } = getSignoMeta(ind);
  return fmtValorSigno(ind["Meta"] as number | null | undefined, signo, dec);
}

/** Formatea Ejecución usando los campos de signo del indicador. */
export function fmtEjecucion(ind: Record<string, unknown>): string {
  const { signo, dec } = getSignoEjec(ind);
  return fmtValorSigno(ind["Ejecucion"] as number | null | undefined, signo, dec);
}
