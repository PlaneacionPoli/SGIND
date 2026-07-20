import { ReactNode } from "react";
import {
  TrendingUp,
  GraduationCap,
  Zap,
  Leaf,
  Target,
  Shield,
  BarChart3,
} from "lucide-react";

const ICON_MAP: Record<string, ({ size, style, className }: { size: number; style?: React.CSSProperties; className?: string }) => ReactNode> = {
  rocket: TrendingUp,
  chart: BarChart3,
  medal: Target,
  bulb: Zap,
  leaf: Leaf,
  graduation: GraduationCap,
  shield: Shield,
};

export interface StrategyCardData {
  linea: string;
  icon: string;
  color: string;
  count: number;
  cumplimiento: number;
  unit_label: string;
  historico: { anio: number; cumplimiento: number }[];
  n_indicadores?: number;
  n_proyectos?: number;
  n_retos?: number;
}

interface StrategyCardProps {
  card: StrategyCardData;
}

export function StrategyCard({ card }: StrategyCardProps) {
  const IconComponent = ICON_MAP[card.icon];

  return (
    <div
      className="group relative overflow-hidden rounded-2xl shadow-md transition-all duration-300 hover:shadow-2xl hover:scale-105 cursor-pointer flex flex-col items-center justify-center aspect-square"
      style={{
        background: card.color,
      }}
    >
      <div className="absolute inset-0 bg-black opacity-0 group-hover:opacity-10 transition-opacity duration-300" />

      <div className="relative z-10 flex flex-col items-center justify-center h-full gap-6 p-6 text-center">
        <div className="transition-transform duration-300 group-hover:scale-125 group-hover:-rotate-12">
          {IconComponent && (
            <IconComponent size={56} style={{ color: "#ffffff" }} strokeWidth={1.5} />
          )}
        </div>

        <h3 className="text-lg sm:text-xl font-bold text-white leading-tight">
          {card.linea}
        </h3>
      </div>

      <div className="absolute bottom-0 left-0 right-0 h-1 bg-white opacity-0 group-hover:opacity-30 transition-opacity duration-300" />
    </div>
  );
}

export function StrategyCardGrid({ cards }: { cards: StrategyCardData[] }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 animate-in fade-in-50 duration-500">
      {cards.map((card, idx) => (
        <div
          key={card.linea}
          style={{
            animation: `fadeInUp 0.5s ease-out ${idx * 0.08}s both`,
          }}
        >
          <StrategyCard card={card} />
        </div>
      ))}
      <style>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(15px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
}
