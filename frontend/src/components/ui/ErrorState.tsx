import { cn } from "@/lib/utils";
import { AlertTriangle, RefreshCw, ServerCrash, WifiOff } from "lucide-react";

interface ErrorStateProps {
  title?: string;
  description?: string;
  onRetry?: () => void;
  className?: string;
  variant?: "generic" | "network" | "server";
  inline?: boolean;
}

const VARIANTS = {
  generic: {
    icon: <AlertTriangle className="w-9 h-9 text-semaforo-alerta" />,
    title: "Ocurrió un error",
    description: "No se pudo cargar la información. Intenta nuevamente.",
  },
  network: {
    icon: <WifiOff className="w-9 h-9 text-semaforo-alerta" />,
    title: "Sin conexión",
    description: "Verifica tu conexión a internet e intenta de nuevo.",
  },
  server: {
    icon: <ServerCrash className="w-9 h-9 text-semaforo-peligro" />,
    title: "Error del servidor",
    description: "El servicio no está disponible temporalmente.",
  },
} as const;

export function ErrorState({
  title,
  description,
  onRetry,
  className,
  variant = "generic",
  inline = false,
}: ErrorStateProps) {
  const defaults = VARIANTS[variant];

  if (inline) {
    return (
      <div
        className={cn(
          "flex items-center gap-3 rounded-lg border border-semaforo-alerta-bg bg-semaforo-alerta-bg px-4 py-3",
          className
        )}
      >
        <AlertTriangle className="w-4 h-4 text-semaforo-alerta flex-shrink-0" />
        <p className="text-sm text-amber-800">{title ?? defaults.title}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="ml-auto text-xs font-medium text-amber-700 hover:text-amber-900 flex items-center gap-1"
          >
            <RefreshCw className="w-3 h-3" /> Reintentar
          </button>
        )}
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-4 py-14 px-6 text-center",
        className
      )}
    >
      <div className="rounded-full bg-semaforo-alerta-bg p-4 border border-amber-100">
        {defaults.icon}
      </div>
      <div className="space-y-1 max-w-xs">
        <p className="text-sm font-semibold text-slate-700">{title ?? defaults.title}</p>
        <p className="text-xs text-slate-400">{description ?? defaults.description}</p>
      </div>
      {onRetry && (
        <button onClick={onRetry} className="btn-secondary gap-2">
          <RefreshCw className="w-4 h-4" />
          Reintentar
        </button>
      )}
    </div>
  );
}
