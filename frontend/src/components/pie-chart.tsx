import { z } from "zod";
import {
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

export const PieChartProps = z.object({
  title: z.string().describe("Chart title"),
  data: z
    .array(
      z.object({
        name: z.string().describe("Slice label"),
        value: z.number().describe("Numeric value"),
      })
    )
    .describe("Array of data points"),
});

type PieChartPropsType = z.infer<typeof PieChartProps>;

const COLORS = ["#6366f1", "#8b5cf6", "#a78bfa", "#c4b5fd", "#ddd6fe"];

export function PieChart({ title, data }: PieChartPropsType) {
  // `render` fires on every streaming update, so `data` may be undefined or
  // partially filled before the agent finishes emitting the tool call.
  const points = data ?? [];

  return (
    <div style={{ marginTop: 8, maxWidth: 400 }}>
      <div style={{ fontWeight: 600, marginBottom: 8 }}>{title}</div>
      {points.length === 0 ? (
        <div style={{ fontSize: 14, color: "#888" }}>Loading chart…</div>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <RechartsPieChart>
            <Pie data={points} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90}>
              {points.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </RechartsPieChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
