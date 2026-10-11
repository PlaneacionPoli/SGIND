"use client";

import { Bar, BarChart, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { COLOR } from "@/components/seguimiento/constants";
import { Vacio } from "@/components/seguimiento/Panel";
import type { OMFila, OMPorProceso } from "@/lib/types";
import { estadoOM } from "./utils";

const COLOR_CON_OM = "#2563eb";

interface ProcesoProps {
  datos: OMPorProceso[];
  seleccionado: string;
  onSeleccionar: (proceso: string) => void;
}

/** Barras horizontales por proceso: con OM / sin OM. Un clic filtra la tabla por ese proceso. */
export function ProcesoChart({ datos, seleccionado, onSeleccionar }: ProcesoProps) {
  if (datos.length === 0) return <Vacio texto="No hay indicadores en riesgo en este corte." />;
  const alto = Math.max(200, datos.length * 36 + 60);
  const clic = (d: unknown) => {
    const item = d as { proceso?: string; payload?: { proceso?: string } };
    const p = item?.payload?.proceso ?? item?.proceso;
    if (p) onSeleccionar(p === seleccionado ? "Todos" : p);
  };
  return (
    <div style={{ height: alto }} role="img" aria-label="Indicadores en riesgo por proceso, con y sin OM">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={datos} layout="vertical" margin={{ left: 8, right: 16, top: 4, bottom: 4 }} barCategoryGap={6}>
          <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11, fill: COLOR.texto }} axisLine={false} tickLine={false} />
          <YAxis
            type="category"
            dataKey="proceso"
            width={170}
            tick={{ fontSize: 11, fill: "#334155" }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v: string) => (v.length > 26 ? `${v.slice(0, 25)}…` : v)}
          />
          <Tooltip cursor={{ fill: "#f1f5f9" }} />
          <Legend verticalAlign="top" align="right" iconType="circle" wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="sin_om" name="Sin OM" stackId="a" fill={COLOR.critico} cursor="pointer" onClick={clic}>
            {datos.map((d) => (
              <Cell key={d.proceso} fillOpacity={seleccionado === "Todos" || seleccionado === d.proceso ? 1 : 0.3} />
            ))}
          </Bar>
          <Bar dataKey="con_om" name="Con OM" stackId="a" fill={COLOR_CON_OM} radius={[0, 4, 4, 0]} cursor="pointer" onClick={clic}>
            {datos.map((d) => (
              <Cell key={d.proceso} fillOpacity={seleccionado === "Todos" || seleccionado === d.proceso ? 1 : 0.3} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

interface DonaProps {
  filas: OMFila[];
  colores: Record<string, string>;
  textoVacio: string;
}

export function agruparPorTipoAccion(filas: OMFila[]): Array<{ nombre: string; valor: number }> {
  const cuenta = new Map<string, number>();
  for (const f of filas) {
    if (estadoOM(f) === "sin_om") continue;
    cuenta.set(f.tipo_accion, (cuenta.get(f.tipo_accion) ?? 0) + 1);
  }
  return Array.from(cuenta, ([nombre, valor]) => ({ nombre, valor })).sort((a, b) => b.valor - a.valor);
}

/** Dona por tipo de acción de las OM registradas. */
export function TipoAccionDona({ filas, colores, textoVacio }: DonaProps) {
  const datos = agruparPorTipoAccion(filas);
  if (datos.length === 0) return <Vacio texto={textoVacio} />;
  return (
    <div className="h-[220px]" role="img" aria-label="OM registradas por tipo de acción">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={datos} dataKey="valor" nameKey="nombre" innerRadius={52} outerRadius={80} paddingAngle={2}>
            {datos.map((d) => (
              <Cell key={d.nombre} fill={colores[d.nombre] ?? "#94a3b8"} />
            ))}
          </Pie>
          <Tooltip />
          <Legend verticalAlign="bottom" iconType="circle" wrapperStyle={{ fontSize: 12 }} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
