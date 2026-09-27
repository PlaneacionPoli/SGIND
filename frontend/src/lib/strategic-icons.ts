import { ReactNode } from "react";
import { TrendingUp, GraduationCap, Zap, Leaf, Target, Shield, BarChart3 } from "lucide-react";

export type StrategicIconComponent = (props: {
  size: number;
  style?: React.CSSProperties;
  className?: string;
  strokeWidth?: number;
}) => ReactNode;

export const STRATEGIC_ICON_MAP: Record<string, StrategicIconComponent> = {
  rocket: TrendingUp,
  chart: BarChart3,
  medal: Target,
  bulb: Zap,
  leaf: Leaf,
  graduation: GraduationCap,
  shield: Shield,
};
