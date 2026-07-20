interface PagePlaceholderProps {
  title: string;
  description: string;
  phase?: string;
}

export function PagePlaceholder({ title, description, phase = "Fase 5" }: PagePlaceholderProps) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">{title}</h2>
        <p className="mt-1 text-slate-600">{description}</p>
      </div>
      <div className="rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center">
        <p className="text-sm text-slate-500">
          Módulo en construcción — implementación planificada en {phase}
        </p>
      </div>
    </div>
  );
}
