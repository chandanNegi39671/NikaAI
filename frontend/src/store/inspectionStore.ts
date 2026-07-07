/**
 * src/store/inspectionStore.ts
 * ─────────────────────────────
 * Zustand global store for inspection session state.
 * Persists the last API result, captured image, and inspection history.
 */

import { create } from 'zustand'
import type { PredictResponse, HistoryEntry, Severity } from '../types'

interface InspectionStore {
  // Current session
  lastResult: PredictResponse | null
  capturedImageUrl: string | null
  isProcessing: boolean
  sessionId: string
  error: string | null
  liveMode: boolean

  // History
  history: HistoryEntry[]

  // Backend health (mirrored/synced or managed)
  modelLoaded: boolean
  backendUptime: string
  backendOnline: boolean

  // Actions
  setResult: (result: PredictResponse, imageUrl: string) => void
  setProcessing: (v: boolean) => void
  setError: (msg: string | null) => void
  clearSession: () => void
  addToHistory: (entry: HistoryEntry) => void
  setHealthStatus: (loaded: boolean, uptime: string) => void
  setBackendOnline: (online: boolean) => void
  setLiveMode: (live: boolean) => void
  resetHistory: () => void
}

const generateSessionId = () =>
  `#NK-${Math.floor(Math.random() * 9000 + 1000)}-${Math.random().toString(36).slice(2, 4).toUpperCase()}`

export const useInspectionStore = create<InspectionStore>((set) => ({
  lastResult: null,
  capturedImageUrl: null,
  isProcessing: false,
  sessionId: generateSessionId(),
  error: null,
  liveMode: false,
  history: [],
  modelLoaded: false,
  backendUptime: '--',
  backendOnline: false,

  setResult: (result, imageUrl) =>
    set((state) => {
      const severity: Severity =
        result.detections.length === 0
          ? 'Resolved'
          : result.detections[0].confidence > 0.8
          ? 'Critical'
          : 'Warning'

      const defectName =
        result.detections.length > 0
          ? result.detections[0].class.replace(/_/g, ' ')
          : 'No Defects Found'

      const newEntry: HistoryEntry = {
        id: state.sessionId,
        timestamp: new Date().toLocaleString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          month: 'short',
          day: 'numeric',
        }),
        severity,
        defectName,
        imageDataUrl: imageUrl,
        result,
        inferenceTimeMs: result.inference_time_ms,
      }

      return {
        lastResult: result,
        capturedImageUrl: imageUrl,
        isProcessing: false,
        error: null,
        history: [newEntry, ...state.history].slice(0, 50),
        sessionId: generateSessionId(),
      }
    }),

  setProcessing: (v) => set({ isProcessing: v }),

  setError: (msg) => set({ error: msg, isProcessing: false }),

  clearSession: () =>
    set({
      lastResult: null,
      capturedImageUrl: null,
      error: null,
    }),

  addToHistory: (entry) =>
    set((state) => ({ history: [entry, ...state.history].slice(0, 50) })),

  setHealthStatus: (loaded, uptime) =>
    set({ modelLoaded: loaded, backendUptime: uptime }),

  setBackendOnline: (online) => set({ backendOnline: online }),

  setLiveMode: (live) => set({ liveMode: live }),

  resetHistory: () => set({ history: [] }),
}))
