import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { ConstructorStanding } from "../services/api";

// F1 constructor brand colors — matched to 2023 season teams
const CONSTRUCTOR_COLORS: Record<string, string> = {
  "Red Bull Racing": "#3671C6",
  "Mercedes":        "#27F4D2",
  "Ferrari":         "#E8002D",
  "McLaren":         "#FF8000",
  "Aston Martin":    "#358C75",
  "Alpine":          "#FF87BC",
  "Williams":        "#64C4FF",
  "AlphaTauri":      "#5E8FAA",
  "Alfa Romeo":      "#C92D4B",
  "Haas F1 Team":    "#B6BABD",
};

const DEFAULT_COLOR = "#555961";

interface ConstructorChartProps {
  data: ConstructorStanding[];
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ value: number; name: string }>;
  label?: string;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-name">{label}</div>
      <div className="chart-tooltip-val">{payload[0].value.toLocaleString()} pts</div>
    </div>
  );
}

export default function ConstructorChart({ data }: ConstructorChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart
        data={data}
        margin={{ top: 8, right: 16, left: -10, bottom: 60 }}
        barCategoryGap="30%"
      >
        <CartesianGrid vertical={false} stroke="#1d1f26" />
        <XAxis
          dataKey="name"
          tick={{ fill: "#636770", fontSize: 10 }}
          axisLine={false}
          tickLine={false}
          angle={-35}
          textAnchor="end"
          interval={0}
        />
        <YAxis
          tick={{ fill: "#636770", fontSize: 10 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v: number) => `${v}`}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
        <Bar dataKey="total_points" radius={[4, 4, 0, 0]}>
          {data.map((entry) => (
            <Cell
              key={entry.name}
              fill={CONSTRUCTOR_COLORS[entry.name] ?? DEFAULT_COLOR}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
