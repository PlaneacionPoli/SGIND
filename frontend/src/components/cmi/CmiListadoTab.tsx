"use client";

import { useMemo, useState } from "react";
import type { Indicator } from "@/lib/types";
import { fmtPct, NivelBadge } from "@/components/cmi/nivelUtils";
import { fmtMeta, fmtEjecucion } from "@/lib/formatValor";

interface CmiListadoTabProps {
  indicadores: Indicator[];
  onOpenFicha?: (id: string) => void;
}

const PAGE_SIZES = [25, 50, 100];

export function CmiListadoTab({ indicadores, onOpenFicha }: CmiListadoTabProps) {
  const [linea, setLinea] = useState("Todas");
  const [objetivo, setObjetivo] = useState("Todos");
  const [estado, setEstado] = useState("Todos");
  const [busqueda, setBusqueda] = useState("");
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);

  const lineas = useMemo(() => {
    const set = new Set(indicadores.map((i) => i.Linea).filter(Boolean) as string[]);
    return ["Todas", ...Array.from(set).sort()];
  }, [indicadores]);

  const objetivos = useMemo(() => {
    const set = new Set(indicadores.map((i) => (i as Record<string, unknown>).Objetivo as string).filter(Boolean));
    return ["Todos", ...Array.from(set).sort()];
  }, [indicadores]);

  const filtered = useMemo(() => {
    return indicadores.filter((ind) => {
      const obj = (ind as Record<string, unknown>).Objetivo as string | undefined;
      const nivel = ind["Nivel de cumplimiento"] as string | undefined;
      if (linea !== "Todas" && ind.Linea !== linea) return false;
      if (objetivo !== "Todos" && obj !== objetivo) return false;
      if (estado !== "Todos" && nivel !== estado) return false;
      if (busqueda.trim() && !String(ind.Indicador ?? "").toLowerCase().includes(busqueda.trim().toLowerCase())) {
        return false;
      }
      return true;
    });
  }, [indicadores, linea, objetivo, estado, busqueda]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const pageItems = filtered.slice(page * pageSize, (page + 1) * pageSize);

  const exportCsv = () => {
    const headers = ["Id", "Indicador", "Linea", "Objetivo", "Meta", "Ejecucion", "cumplimiento_pct", "Nivel"];
    const rows = filtered.map((ind) => {
      const rec = ind as Record<string, unknown>;
      return headers
        .map((h) => {
          let val: unknown;
          if (h === "Meta") val = fmtMeta(rec);
          else if (h === "Ejecucion") val = fmtEjecucion(rec);
          else val = rec[h];
          return `"${String(val ?? "").replace(/"/g, '""')}"`;
        })
        .join(",");
    });
    const blob = new Blob([[headers.join(","), ...rows].join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "indicadores_cmi.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-lg font-semibold text-slate-800">Listado de Indicadores</h3>
        <button
          type="button"
          onClick={exportCsv}
          className="rounded-lg bg-poli-navy px-4 py-2 text-sm font-medium text-white hover:bg-poli-blue"
        >
          Exportar CSV
        </button>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <FilterSelect label="Línea" value={linea} options={lineas} onChange={(v) => { setLinea(v); setPage(0); }} />
        <FilterSelect label="Objetivo" value={objetivo} options={objetivos} onChange={(v) => { setObjetivo(v); setPage(0); }} />
        <FilterSelect
          label="Estado"
          value={estado}
          options={["Todos", "Peligro", "Alerta", "Cumplimiento", "Sobrecumplimiento", "Pendiente de reporte"]}
          onChange={(v) => { setEstado(v); setPage(0); }}
        />
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-slate-600">Buscar indicador</span>
          <input
            type="search"
            value={busqueda}
            onChange={(e) => { setBusqueda(e.target.value); setPage(0); }}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            placeholder="Nombre del indicador..."
          />
        </label>
      </div>

      <p className="text-sm text-slate-500">
        {filtered.length} indicador{filtered.length !== 1 ? "es" : ""} encontrado{filtered.length !== 1 ? "s" : ""}
      </p>

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-poli-navy text-white">
            <tr>
              <th className="px-3 py-2">Código</th>
              <th className="px-3 py-2">Indicador</th>
              <th className="px-3 py-2">Línea</th>
              <th className="px-3 py-2">Meta</th>
              <th className="px-3 py-2">Ejecución</th>
              <th className="px-3 py-2">%</th>
              <th className="px-3 py-2">Estado</th>
              <th className="px-3 py-2" />
            </tr>
          </thead>
          <tbody>
            {pageItems.map((ind) => (
              <tr key={ind.Id ?? ind.Indicador} className="border-t border-slate-100 hover:bg-slate-50">
                <td className="px-3 py-2 text-xs text-slate-500">{ind.Id}</td>
                <td className="max-w-xs truncate px-3 py-2 font-medium text-slate-800">{ind.Indicador}</td>
                <td className="px-3 py-2 text-xs">{ind.Linea}</td>
                <td className="px-3 py-2">{fmtMeta(ind as Record<string, unknown>)}</td>
                <td className="px-3 py-2">{fmtEjecucion(ind as Record<string, unknown>)}</td>
                <td className="px-3 py-2 font-semibold">{fmtPct(ind.cumplimiento_pct as number | undefined)}</td>
                <td className="px-3 py-2">
                  <NivelBadge nivel={ind["Nivel de cumplimiento"] as string | undefined} />
                </td>
                <td className="px-3 py-2">
                  {ind.Id && onOpenFicha && (
                    <button
                      type="button"
                      onClick={() => onOpenFicha(String(ind.Id))}
                      className="text-xs font-semibold text-poli-blue hover:underline"
                    >
                      Ficha
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
        <div className="flex items-center gap-2">
          <span className="text-slate-500">Filas por página</span>
          <select
            value={pageSize}
            onChange={(e) => { setPageSize(Number(e.target.value)); setPage(0); }}
            className="rounded border border-slate-300 px-2 py-1"
          >
            {PAGE_SIZES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            disabled={page === 0}
            onClick={() => setPage((p) => p - 1)}
            className="rounded border border-slate-300 px-3 py-1 disabled:opacity-40"
          >
            Anterior
          </button>
          <span className="text-slate-600">
            Página {page + 1} de {totalPages}
          </span>
          <button
            type="button"
            disabled={page >= totalPages - 1}
            onClick={() => setPage((p) => p + 1)}
            className="rounded border border-slate-300 px-3 py-1 disabled:opacity-40"
          >
            Siguiente
          </button>
        </div>
      </div>
    </div>
  );
}

function FilterSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
}) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="font-medium text-slate-600">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-md border border-slate-300 px-3 py-2 text-sm"
      >
        {options.map((o) => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
    </label>
  );
}
