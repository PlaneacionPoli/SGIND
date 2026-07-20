const VISTA_LABELS: Record<string, string> = {
  indicadores: "Indicadores",
  proyectos: "Proyectos",
  retos: "Plan de Retos",
  consolidado: "Consolidado",
};

interface VistaSelectorProps {
  vista: string;
  vistas?: string[];
  onChange: (vista: string) => void;
}

export function VistaSelector({ vista, vistas = ["consolidado", "retos", "proyectos", "indicadores"], onChange }: VistaSelectorProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {vistas.map((v) => (
        <button
          key={v}
          type="button"
          onClick={() => onChange(v)}
          className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
            vista === v
              ? "bg-poli-blue text-white shadow-sm"
              : "bg-slate-100 text-slate-600 hover:bg-slate-200"
          }`}
        >
          {VISTA_LABELS[v] ?? v}
        </button>
      ))}
    </div>
  );
}
