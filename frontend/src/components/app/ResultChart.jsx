
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

export default function ResultChart({ data, visualization }) {
  // Do not force table-shaped results into a chart.
  if (visualization?.type === 'table') return null;

  if (!Array.isArray(data) || data.length === 0) return null;

  const keys = Object.keys(data[0] || {});

  // Prefer numeric data for the Y-axis.
  const yKey = keys.find(
    (key) => typeof data[0][key] === 'number'
  );

  // A meaningful chart needs both a category and a numeric value.
  const xKey = keys.find((key) => key !== yKey);

  if (!xKey || !yKey) return null;

  return (
    <section className="panel">
      <h3>{visualization?.title || 'Result visualization'}</h3>

      <div style={{ width: '100%', height: 280 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{ top: 12, right: 16, left: 8, bottom: 40 }}
          >
            <CartesianGrid strokeDasharray="3 3" opacity={0.2} />

            <XAxis
              dataKey={xKey}
              angle={-25}
              textAnchor="end"
              interval="preserveStartEnd"
              height={65}
            />

            <YAxis />

            <Tooltip />

            <Bar
              dataKey={yKey}
              fill="var(--accent)"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
