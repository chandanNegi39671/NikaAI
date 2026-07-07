/**
 * src/store/metricsStore.ts
 * ──────────────────────────
 * Zustand store for live inspection performance metrics.
 * Updated on every inference frame by the useInference hook.
 */

import { create } from 'zustand'
import type { MetricsSnapshot } from '../types'

interface MetricsStore extends MetricsSnapshot {
  updateMetrics: (patch: Partial<MetricsSnapshot>) => void
  recordInferenceResult: (opts: {
    inferenceTimeMs: number
    latencyMs: number
    detectionCount: number
  }) => void
  setBackendStatus: (online: boolean, modelLoaded: boolean, uptime: string, version?: string) => void
  resetMetrics: () => void
}

const initialMetrics: MetricsSnapshot = {
  fps: 0,
  latencyMs: 0,
  inferenceTimeMs: 0,
  frameCount: 0,
  detectionCount: 0,
  overallStatus: 'IDLE',
  backendOnline: false,
  modelLoaded: false,
  backendUptime: '--',
  modelVersion: '--',
  lastUpdated: 0,
}

export const useMetricsStore = create<MetricsStore>((set, get) => ({
  ...initialMetrics,

  updateMetrics: (patch) => set((s) => ({ ...s, ...patch })),

  recordInferenceResult: ({ inferenceTimeMs, latencyMs, detectionCount }) =>
    set((s) => {
      const now = Date.now()
      const elapsed = now - s.lastUpdated
      const fps = elapsed > 0 ? Math.min(Math.round(1000 / elapsed), 60) : s.fps

      return {
        inferenceTimeMs,
        latencyMs,
        detectionCount,
        fps,
        frameCount: s.frameCount + 1,
        overallStatus: detectionCount > 0 ? 'FAIL' : 'PASS',
        lastUpdated: now,
      }
    }),

  setBackendStatus: (online, modelLoaded, uptime, version) =>
    set((s) => ({
      backendOnline: online,
      modelLoaded,
      backendUptime: uptime,
      modelVersion: version ?? s.modelVersion,
    })),

  resetMetrics: () => set(initialMetrics),
}))
