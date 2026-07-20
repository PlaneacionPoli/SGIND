const MESES = [
  "Enero",
  "Febrero",
  "Marzo",
  "Abril",
  "Mayo",
  "Junio",
  "Julio",
  "Agosto",
  "Septiembre",
  "Octubre",
  "Noviembre",
  "Diciembre",
];

interface FilterBarProps {
  anio: number;
  periodo: string;
  years?: number[];
  onAnioChange: (anio: number) => void;
  onPeriodoChange: (periodo: string) => void;
}

export function FilterBar({
  anio,
  periodo,
  years,
  onAnioChange,
  onPeriodoChange,
}: FilterBarProps) {
  const currentYear = new Date().getFullYear();
  const yearOptions = years?.length ? years : Array.from({ length: 6 }, (_, i) => currentYear - i);

  return (
    <div className="flex flex-wrap items-end gap-4 rounded-lg border border-slate-200 bg-white p-4">
      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium text-slate-600">Año</span>
        <select
          value={anio}
          onChange={(e) => onAnioChange(Number(e.target.value))}
          className="rounded-md border border-slate-300 px-3 py-2 text-sm"
        >
          {yearOptions.map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
      </label>
      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium text-slate-600">Periodo</span>
        <select
          value={periodo}
          onChange={(e) => onPeriodoChange(e.target.value)}
          className="rounded-md border border-slate-300 px-3 py-2 text-sm"
        >
          <option value="">Todos</option>
          {MESES.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
