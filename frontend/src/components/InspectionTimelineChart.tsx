/**
 * src/components/InspectionTimelineChart.tsx
 * ──────────────────────────────────────────
 * Recharts-based area chart displaying defect rate or pass rate trends.
 * Supports 7D and 30D toggling with a premium glowing area highlight.
 */

import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts'
import type { DailyStats } from '../types'

interface InspectionTimelineChartProps {
  data: DailyStats[]
}

export default function InspectionTimelineChart({ data }: InspectionTimelineChartProps) {
  // Map data to Recharts format
  const chartData = data.map((d) => ({
    name: d.date,
    'Defect Rate': Math.round(d.defectCount / d.totalInspections * 1000) / 10,
    'Pass Rate': d.passRate,
    Inspections: d.totalInspections,
  }))

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={chartData}
          margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
        >
          <defs>
            <linearGradient id="timelineAreaGlow" x1="0" y1="0" x2="0" y2="100%">
              <stop offset="0%" stopColor="#fbba64" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#fbba64" stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <XAxis
            dataKey="name"
            stroke="rgba(255,255,255,0.3)"
            fontSize={10}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            stroke="rgba(255,255,255,0.3)"
            fontSize={10}
            domain={[80, 100]}
            tickLine={false}
            axisLine={false}
            tickFormatter={(val) => `${val}%`}
          />
          <Tooltip
            cursor={{ stroke: 'rgba(251, 186, 100, 0.2)', strokeWidth: 1 }}
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const dataPoint = payload[0].payload
                return (
                  <div className="bg-surface-container-high border border-primary/20 p-3 rounded-xl shadow-glass text-left">
                    <p className="font-display-mono text-[10px] text-primary uppercase">
                      {dataPoint.name}
                    </p>
                    <p className="text-white font-bold text-sm mt-1">
                      Pass Rate: {dataPoint['Pass Rate']}%
                    </p>
                    <p className="text-on-surface-variant/80 text-xs mt-0.5">
                      Inspections: {dataPoint.Inspections}
                    </p>
                    <p className="text-error text-[10px] font-display-mono mt-1">
                      Defect Rate: {dataPoint['Defect Rate']}%
                    </p>
                  </div>
                )
              }
              return null
            }}
          />
          <Area
            type="monotone"
            dataKey="Pass Rate"
            stroke="#fbba64"
            strokeWidth={3}
            fillOpacity={1}
            fill="url(#timelineAreaGlow)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
