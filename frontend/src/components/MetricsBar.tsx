/**
 * src/components/MetricsBar.tsx
 * ──────────────────────────────
 * Live KPI bar displaying FPS, latency, model status, and pass/fail indicators.
 */

import { motion } from 'framer-motion'
import LedPulse from './LedPulse'
import StatusBadge from './StatusBadge'

interface MetricsBarProps {
  fps: number
  latencyMs: number
  inferenceTimeMs: number
  detectionCount: number
  backendOnline: boolean
  modelLoaded: boolean
  modelVersion: string
  isLive: boolean
}

export default function MetricsBar({
  fps,
  latencyMs,
  inferenceTimeMs,
  detectionCount,
  backendOnline,
  modelLoaded,
  modelVersion,
  isLive,
}: MetricsBarProps) {
  const status = detectionCount > 0 ? 'Fail' : 'Pass'

  return (
    <div className="glass-panel border border-primary/20 w-full rounded-2xl p-4 md:p-6 shadow-glass">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-6 items-center">
        
        {/* Pass / Fail Status */}
        <div className="flex flex-col gap-1 border-r border-white/5 pr-4">
          <span className="font-label-sm text-label-sm text-on-surface-variant uppercase opacity-60">
            Inspection
          </span>
          <div className="flex items-center gap-2">
            <StatusBadge severity={status} className="text-sm px-3 py-1 font-bold" />
            {detectionCount > 0 && (
              <span className="font-display-mono text-xs text-error font-bold">
                ({detectionCount} defects)
              </span>
            )}
          </div>
        </div>

        {/* Latency & Inference Time */}
        <div className="flex flex-col gap-1 border-r border-white/5 pr-4">
          <span className="font-label-sm text-label-sm text-on-surface-variant uppercase opacity-60">
            Performance
          </span>
          <div className="flex items-baseline gap-2">
            <span className="font-display-mono text-lg font-bold text-on-surface">
              {latencyMs > 0 ? `${latencyMs}ms` : '--'}
            </span>
            <span className="text-[10px] text-on-surface-variant/40 font-display-mono">
              (AI: {inferenceTimeMs > 0 ? `${inferenceTimeMs.toFixed(0)}ms` : '--'})
            </span>
          </div>
        </div>

        {/* FPS & Feed Type */}
        <div className="flex flex-col gap-1 md:border-r border-white/5 md:pr-4">
          <span className="font-label-sm text-label-sm text-on-surface-variant uppercase opacity-60">
            Frame Feed
          </span>
          <div className="flex items-center gap-2">
            <span className="font-display-mono text-lg font-bold text-on-surface">
              {isLive ? `${fps} FPS` : 'STATIC'}
            </span>
            {isLive && <LedPulse color="primary" size="sm" />}
          </div>
        </div>

        {/* Model info */}
        <div className="flex flex-col gap-1 border-r border-white/5 pr-4">
          <span className="font-label-sm text-label-sm text-on-surface-variant uppercase opacity-60">
            AI Engine
          </span>
          <span className="font-display-mono text-xs text-primary-fixed-dim truncate">
            YOLOv8 ({modelVersion})
          </span>
        </div>

        {/* System connection Status */}
        <div className="flex flex-col gap-1 col-span-2 md:col-span-1 items-start md:items-end">
          <span className="font-label-sm text-label-sm text-on-surface-variant uppercase opacity-60">
            API Gateway
          </span>
          <div className="flex items-center gap-2">
            <span className="font-display-mono text-xs uppercase">
              {backendOnline ? (modelLoaded ? 'OPERATIONAL' : 'MODEL OFFLINE') : 'DISCONNECTED'}
            </span>
            <div
              className={`w-2.5 h-2.5 rounded-full ${
                backendOnline && modelLoaded ? 'bg-primary animate-led-pulse' : 'bg-error'
              }`}
            />
          </div>
        </div>

      </div>
    </div>
  )
}
