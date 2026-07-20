"use client";

import { RotateCcw } from "lucide-react";

interface CmiProcesosFiltersProps {
  anio: number;
  mes: number;
  anios: number[];
  meses: number[];
  mesesNombres: string[];
  unidades: string[];
  procesos: string[];
  subprocesos: string[];
  clasificaciones: string[];
  frecuencias: string[];
  unidad: string;
  proceso: string;
  subproceso: string;
  clasificacion: string;
  frecuencia: string;
  onAnioChange: (anio: number) => void;
  onMesChange: (mes: number) => void;
  onUnidadChange: (v: string) => void;
  onProcesoChange: (v: string) => void;
  onSubprocesoChange: (v: string) => void;
  onClasificacionChange: (v: string) => void;
  onFrecuenciaChange: (v: string) => void;
  onReset?: () => void;
}

export function CmiProcesosFilters(props: CmiProcesosFiltersProps) {
  const {
    anio,
    mes,
    anios,
    meses,
    mesesNombres,
    unidades,
    procesos,
    subprocesos,
    clasificaciones,
    frecuencias,
    unidad,
    proceso,
    subproceso,
    clasificacion,
    frecuencia,
    onAnioChange,
    onMesChange,
    onUnidadChange,
    onProcesoChange,
    onSubprocesoChange,
    onClasificacionChange,
    onFrecuenciaChange,
    onReset,
  } = props;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-xs font-bold uppercase tracking-wide text-slate-600">Filtros</h3>
        {onReset && (
          <button
            type="button"
            onClick={onReset}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-poli-navy transition hover:bg-slate-50"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Restablecer
          </button>
        )}
      </div>
      <div className="grid gap-3 lg:grid-cols-2">
        <SegmentedGroup
          label="Año"
          value={anio}
          options={anios.map((y) => ({ value: y, label: String(y) }))}
          onChange={(v) => onAnioChange(Number(v))}
        />
        <SegmentedGroup
          label="Mes"
          value={mes}
          options={meses.map((m) => ({
            value: m,
            label: mesesNombres[m - 1] ?? String(m),
          }))}
          onChange={(v) => onMesChange(Number(v))}
        />
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <SelectFilter label="Unidad" value={unidad} options={unidades} onChange={onUnidadChange} />
        <SelectFilter label="Proceso" value={proceso} options={procesos} onChange={onProcesoChange} />
        <SelectFilter label="Subproceso" value={subproceso} options={subprocesos} onChange={onSubprocesoChange} />
        <SelectFilter
          label="Clasificación"
          value={clasificacion}
          options={clasificaciones}
          onChange={onClasificacionChange}
        />
        <SelectFilter label="Frecuencia" value={frecuencia} options={frecuencias} onChange={onFrecuenciaChange} />
      </div>
    </div>
  );
}

function SegmentedGroup<T extends string | number>({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (v: T) => void;
}) {
  return (
    <div>
      <p className="mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-500">{label}</p>
      <div className="inline-flex max-w-full flex-wrap gap-1 rounded-xl bg-slate-100 p-1">
        {options.map((opt) => {
          const active = opt.value === value;
          return (
            <button
              key={String(opt.value)}
              type="button"
              onClick={() => onChange(opt.value)}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition sm:px-4 sm:py-2 sm:text-sm ${
                active
                  ? "bg-poli-navy text-white shadow-md"
                  : "text-slate-600 hover:bg-white hover:text-slate-900"
              }`}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function SelectFilter({
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
      <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800"
      >
        <option value="Todos">Todos</option>
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </label>
  );
}
