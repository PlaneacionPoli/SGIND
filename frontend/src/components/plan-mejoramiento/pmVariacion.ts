/** Formato y color de una variación porcentual: positiva en verde, negativa en
 * rojo, cero / sin dato en gris. */
export function fmtVariacion(v: number | null | undefined): string {
  if (v == null) return "—";
  return `${v > 0 ? "+" : ""}${fmtNumero(v, 1)}%`;
}

/** Número en formato colombiano: miles con "." y decimales con ",". Se arma a
 * mano (no con Intl) porque es-CO no agrupa los números de 4 cifras. */
export function fmtNumero(v: number, decimales = 0): string {
  const [entero, fraccion] = Math.abs(v).toFixed(decimales).split(".");
  const miles = entero.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  const signo = v < 0 && Number(Math.abs(v).toFixed(decimales)) !== 0 ? "-" : "";
  return `${signo}${miles}${fraccion ? `,${fraccion}` : ""}`;
}

/** Formatea un valor según la unidad de la métrica — misma regla que
 * fmt_valor_plan del backend: ENT sin decimales (con separador de miles),
 * % con su signo, %FRAC es fracción 0-1 que se muestra x100. */
export function fmtValor(v: number | null | undefined, signo: string | null, decimales: number | null): string {
  if (v == null) return "—";
  const dec = decimales ?? 1;
  if (signo === "ENT") return fmtNumero(v, 0);
  if (signo === "%FRAC") return `${fmtNumero(v * 100, dec)}%`;
  if (signo === "%") return `${fmtNumero(v, dec)}%`;
  return fmtNumero(v, dec);
}

export function variacionClass(v: number | null | undefined): string {
  if (v == null || Math.abs(v) < 0.05) return "text-slate-500";
  return v > 0 ? "text-emerald-600" : "text-rose-600";
}

/** Recta de tendencia (mínimos cuadrados) sobre los puntos con dato; todo null
 * si hay menos de dos. Devuelve el valor ajustado por posición de la serie. */
export function lineaTendencia(valores: Array<number | null>): Array<number | null> {
  const pts: Array<[number, number]> = [];
  valores.forEach((v, i) => {
    if (v != null) pts.push([i, v]);
  });
  if (pts.length < 2) return valores.map(() => null);
  const n = pts.length;
  const sx = pts.reduce((a, [x]) => a + x, 0);
  const sy = pts.reduce((a, [, y]) => a + y, 0);
  const sxy = pts.reduce((a, [x, y]) => a + x * y, 0);
  const sxx = pts.reduce((a, [x]) => a + x * x, 0);
  const den = n * sxx - sx * sx;
  const pendiente = den === 0 ? 0 : (n * sxy - sx * sy) / den;
  const intercepto = (sy - pendiente * sx) / n;
  return valores.map((_, i) => intercepto + pendiente * i);
}
