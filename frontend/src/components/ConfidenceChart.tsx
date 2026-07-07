/**
 * src/components/ConfidenceChart.tsx
 * ──────────────────────────────────
 * Bar chart component visualizing YOLO detection confidences using Recharts.
 */

import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts'
import type { Detection } from '../types'

interface ConfidenceChartProps {
  detections: Detection[]
}

export default function ConfidenceChart({ detections }: ConfidenceChartProps) {
  if (detections.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center p-6 text-on-surface-variant/40">
        <span className="material-symbols-outlined text-4xl mb-1 opacity-25">analytics</span>
        <p className="font-display-mono text-[10px] uppercase">No detections to plot</p>
      </div>
    )
  }

  // Prep data for Recharts
  const data = detections.map((d) => ({
    name: d.class.replace(/_/g, ' '),
    confidence: Math.round(d.confidence * 100),
  }))

  const colors = ['#fbba64', '#ffb694', '#90cdff', '#ffb4ab', '#cbe6ff']

  return (
    <div className="w-full h-44">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
        >
          <XAxis
            dataKey="name"
            stroke="rgba(255,255,255,0.4)"
            fontSize={9}
            tickLine={false}
            axisLine={false}
            tickFormatter={(val) => (val.length > 10 ? `${val.slice(0, 10)}.` : val)}
          />
          <YAxis
            stroke="rgba(255,255,255,0.4)"
            fontSize={9}
            domain={[0, 100]}
            tickLine={false}
            axisLine={false}
            tickFormatter={(val) => `${val}%`}
          />
          <Tooltip
            cursor={{ fill: 'rgba(255,255,255,0.04)' }}
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                return (
                  <div className="bg-surface-container border border-primary/20 p-2.5 rounded-lg shadow-xl font-display-mono text-[11px]">
                    <p className="text-on-surface font-semibold capitalize">
                      {payload[0].name}
                    </p>
                    <p className="text-primary font-bold mt-1">
                      Confidence: {payload[0].value}%
                    </p>
                  </div>
                )
              }
              return null
            }}
          />
          <Bar
            dataKey="confidence"
            radius={[4, 4, 0, 0]}
            maxBarSize={45}
          >
            {data.map((_entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={colors[index % colors.length]}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
